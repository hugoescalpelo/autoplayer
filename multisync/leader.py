import socket
import os
import random
import threading
import time
import subprocess
import getpass

# === Configuración de paths según usuario ===
USERNAME = getpass.getuser()
BASE_VIDEO_DIR = f"/home/{USERNAME}/Videos/videos_hd_final"
BASE_AUDIO_DIR = f"/home/{USERNAME}/Music"

VIDEO_SUBFOLDER = "hor"  # Este líder usa horizontal
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"

VIDEO_EXTENSIONS = ('.mp4', '.mov')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg')

followers = set()
followers_lock = threading.Lock()

# === Validadores de extensión ===
def is_valid_video(filename):
    return filename.lower().endswith(VIDEO_EXTENSIONS)

def is_valid_audio(filename):
    return filename.lower().endswith(AUDIO_EXTENSIONS)

# === Beacon UDP para descubrimiento ===
def broadcast_leader():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            sock.sendto(DISCOVERY_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(2)
        except:
            break

# === Servidor TCP para followers ===
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

# === Confirmación de reproducción completada ===
def wait_for_completion(expected):
    received = 0
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', RESPONSE_PORT))
    server.listen(expected)
    while received < expected:
        conn, _ = server.accept()
        data = conn.recv(1024).decode()
        if data == 'done':
            received += 1
    server.close()

# === Audio en segundo plano ===
def play_audio_background(audio_path):
    subprocess.Popen([
        "mpv",
        "--no-video",
        "--loop=no",
        "--quiet",
        "--no-terminal",
        "--audio-device=alsa/hdmi",
        audio_path
    ])

# === Video en pantalla completa sin parpadeos ===
def play_video(video_path):
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
        video_path
    ])

# === Obtener todas las categorías ===
def pick_categories():
    return [d for d in os.listdir(BASE_VIDEO_DIR)
            if os.path.isdir(os.path.join(BASE_VIDEO_DIR, d))]

# === Elegir 3 normales y 1 texto aleatorios ===
def pick_videos(categoria):
    path = os.path.join(BASE_VIDEO_DIR, categoria, VIDEO_SUBFOLDER)
    text_path = os.path.join(BASE_VIDEO_DIR, categoria, f"{VIDEO_SUBFOLDER}_text")

    if not os.path.exists(path) or not os.path.exists(text_path):
        print(f"⚠️ Falta carpeta en categoría: {categoria}")
        return []

    otros = [f for f in os.listdir(path) if is_valid_video(f)]
    textos = [f for f in os.listdir(text_path) if is_valid_video(f)]

    if len(otros) < 3 or len(textos) < 1:
        print(f"⚠️ No hay suficientes videos en {categoria}")
        return []

    seleccionados = random.sample(otros, 3) + [random.choice(textos)]
    return [os.path.join(path, v) for v in seleccionados[:3]] + [os.path.join(text_path, seleccionados[3])]

# === Enviar mensaje a todos los followers registrados ===
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

# === Bucle principal infinito de reproducción ===
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

            send_to_followers("PLAY:" + cat)

            for v in videos:
                print(f"▶️ {os.path.basename(v)}")
                play_video(v)

            wait_for_completion(expected=len(followers))
            send_to_followers("NEXT")

        print("🔁 Ciclo completado. Iniciando otro...")

if __name__ == '__main__':
    main()
