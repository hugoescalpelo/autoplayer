import socket
import os
import random
import threading
import time
import subprocess
import getpass

USERNAME = getpass.getuser()
BASE_VIDEO_DIR = f"/home/{USERNAME}/Videos/videos_hd_final"
BASE_AUDIO_DIR = f"/home/{USERNAME}/Music"

VIDEO_SUBFOLDER = "hor"
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"

VIDEO_EXTENSIONS = ('.mp4', '.mov')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg')

followers = set()
followers_lock = threading.Lock()

category_lock = threading.Event()  # se usa para avanzar de categoría
done_flag = threading.Event()      # se activa cuando el primero termina

def is_valid_video(filename):
    return filename.lower().endswith(VIDEO_EXTENSIONS)

def is_valid_audio(filename):
    return filename.lower().endswith(AUDIO_EXTENSIONS)

def broadcast_leader():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            sock.sendto(DISCOVERY_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(2)
        except:
            break

def follower_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', FOLLOWER_PORT))
    server.listen(10)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_follower, args=(conn, addr), daemon=True).start()

def handle_follower(conn, addr):
    with conn:
        data = conn.recv(1024).decode()
        if data.startswith("REGISTER:"):
            with followers_lock:
                followers.add(addr[0])
        else:
            print(f"⚠️ Mensaje inesperado de {addr}: {data}")

def response_server():
    """Escucha quién termina primero. Al primer 'done' recibido, activa el evento."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', RESPONSE_PORT))
    server.listen(10)
    conn, _ = server.accept()
    data = conn.recv(1024).decode()
    if data == 'done':
        done_flag.set()
    server.close()

def play_audio_background(audio_path):
    try:
        subprocess.Popen([
            "mpv",
            "--no-video",
            "--loop=no",
            "--quiet",
            "--no-terminal",
            "--audio-device=null",
            audio_path
        ])
    except Exception as e:
        print(f"⚠️ Error al reproducir audio: {e}")

def play_video_sequence(videos):
    for video_path in videos:
        subprocess.run([
            "mpv",
            "--fs",
            "--vo=gpu",
            "--hwdec=no",
            "--no-terminal",
            "--quiet",
            "--gapless-audio",
            "--image-display-duration=inf",
            "--no-stop-screensaver",
            "--keep-open=yes",
            video_path
        ])
        time.sleep(1)
    notify_done()

def pick_categories():
    return [d for d in os.listdir(BASE_VIDEO_DIR)
            if os.path.isdir(os.path.join(BASE_VIDEO_DIR, d))]

def pick_videos(categoria):
    path = os.path.join(BASE_VIDEO_DIR, categoria, VIDEO_SUBFOLDER)
    text_path = os.path.join(BASE_VIDEO_DIR, categoria, f"{VIDEO_SUBFOLDER}_text")

    if not os.path.exists(path) or not os.path.exists(text_path):
        return []

    otros = [f for f in os.listdir(path) if is_valid_video(f)]
    textos = [f for f in os.listdir(text_path) if is_valid_video(f)]

    if len(otros) >= 3 and len(textos) >= 1:
        texto_video = random.choice(textos)
        normales = random.sample(otros, 3)
        return [os.path.join(text_path, texto_video)] + [os.path.join(path, v) for v in normales]
    else:
        print(f"⚠️ No suficientes videos en {categoria}")
        return []

def send_to_followers(message):
    with followers_lock:
        for host in list(followers):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, FOLLOWER_PORT))
                    s.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"⚠️ Error al enviar a {host}: {e}")
                followers.remove(host)

def notify_done():
    """El líder también participa como 'follower'"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', RESPONSE_PORT))
            s.sendall(b'done')
    except Exception as e:
        print(f"⚠️ El líder no pudo notificarse a sí mismo: {e}")

def main():
    threading.Thread(target=broadcast_leader, daemon=True).start()
    threading.Thread(target=follower_server, daemon=True).start()

    audio_files = [f for f in os.listdir(BASE_AUDIO_DIR) if is_valid_audio(f)]
    if audio_files:
        audio = random.choice(audio_files)
        play_audio_background(os.path.join(BASE_AUDIO_DIR, audio))
    else:
        print("⚠️ No hay audio en Music/")

    categorias = pick_categories()
    if not categorias:
        print("❌ No se encontraron categorías.")
        return

    while True:
        random.shuffle(categorias)
        send_to_followers("CATEGORIAS:" + ','.join(categorias))

        for cat in categorias:
            print(f"\n🎬 Categoría actual: {cat}")
            videos = pick_videos(cat)
            if not videos:
                continue

            done_flag.clear()
            threading.Thread(target=response_server, daemon=True).start()
            send_to_followers("PLAY:" + cat)

            threading.Thread(target=play_video_sequence, args=(videos,), daemon=True).start()

            # Esperar a que cualquiera (incluso yo) diga "done"
            done_flag.wait()
            send_to_followers("NEXT")

        print("🔁 Ciclo completado. Reiniciando...")

if __name__ == '__main__':
    main()
