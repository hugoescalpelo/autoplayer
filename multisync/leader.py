import socket
import os
import random
import threading
import time
import subprocess
import getpass
from tempfile import NamedTemporaryFile

USERNAME = getpass.getuser()
BASE_VIDEO_DIR = f"/home/{USERNAME}/Videos/videos_hd_final"
BASE_AUDIO_DIR = f"/home/{USERNAME}/Music/audios"  # ajustado según indicación

VIDEO_SUBFOLDER = "hor"
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"

VIDEO_EXTENSIONS = ('.mp4', '.mov')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg')

followers = set()
followers_lock = threading.Lock()
done_flag = threading.Event()

# Verifica si un archivo es un video válido
def is_valid_video(filename):
    return filename.lower().endswith(VIDEO_EXTENSIONS)

# Verifica si un archivo es un audio válido
def is_valid_audio(filename):
    return filename.lower().endswith(AUDIO_EXTENSIONS)

# Anuncia que este dispositivo es el líder por UDP broadcast
def broadcast_leader():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            sock.sendto(DISCOVERY_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(2)
        except:
            break

# Abre un servidor para aceptar followers que se conectan
def follower_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', FOLLOWER_PORT))
    server.listen(10)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_follower, args=(conn, addr), daemon=True).start()

# Maneja los registros de nuevos followers
def handle_follower(conn, addr):
    with conn:
        data = conn.recv(1024).decode()
        if data.startswith("REGISTER:"):
            with followers_lock:
                followers.add(addr[0])
        else:
            print(f"⚠️ Mensaje inesperado de {addr}: {data}")

# Servidor que espera un solo mensaje "done" y activa la bandera
def response_server():
    while True:
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', RESPONSE_PORT))
            server.listen(1)
            conn, _ = server.accept()
            data = conn.recv(1024).decode()
            if data == 'done':
                done_flag.set()
            conn.close()
            server.close()
        except Exception as e:
            print(f"⚠️ Error en response_server: {e}")
            time.sleep(1)

# Reproduce audio en segundo plano sin bloquear
def play_audio_background(audio_path):
    try:
        subprocess.Popen([
            "mpv", "--no-video", "--loop=no", "--quiet",
            "--no-terminal", "--audio-device=null", audio_path
        ])
    except Exception as e:
        print(f"⚠️ Error al reproducir audio: {e}")

# Genera un archivo temporal con la lista de reproducción
def generate_mpv_playlist(video_paths):
    playlist = NamedTemporaryFile(mode='w', delete=False, suffix=".m3u")
    for path in video_paths:
        playlist.write(f"{path}\n")
    playlist.close()
    return playlist.name

# Ejecuta mpv con la lista de reproducción sin cerrar la ventana entre videos
def play_video_sequence_with_mpv(playlist_path):
    subprocess.run([
        "mpv", "--fs", "--vo=gpu", "--hwdec=no", "--no-terminal", "--quiet",
        "--gapless-audio", "--image-display-duration=inf", "--no-stop-screensaver",
        "--keep-open=always", "--loop-playlist=no", f"--playlist={playlist_path}"
    ])
    os.remove(playlist_path)  # Limpia el archivo de lista temporal
    notify_done()

# Obtiene las carpetas disponibles como categorías
def pick_categories():
    return [d for d in os.listdir(BASE_VIDEO_DIR)
            if os.path.isdir(os.path.join(BASE_VIDEO_DIR, d))]

# Selecciona 1 video de texto + 3 normales para una categoría
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

# Envía un mensaje a todos los followers conectados
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

# El líder también envía 'done' como si fuera un follower
def notify_done():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', RESPONSE_PORT))
            s.sendall(b'done')
    except Exception as e:
        print(f"⚠️ El líder no pudo notificarse a sí mismo: {e}")

# Función principal del líder
def main():
    threading.Thread(target=broadcast_leader, daemon=True).start()
    threading.Thread(target=follower_server, daemon=True).start()
    threading.Thread(target=response_server, daemon=True).start()

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
            send_to_followers("PLAY:" + cat)

            playlist_path = generate_mpv_playlist(videos)
            threading.Thread(target=play_video_sequence_with_mpv, args=(playlist_path,), daemon=True).start()

            done_flag.wait()
            send_to_followers("NEXT")

        print("🔁 Ciclo completado. Reiniciando...")

if __name__ == '__main__':
    main()