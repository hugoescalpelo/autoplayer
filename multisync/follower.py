import socket
import os
import random
import threading
import time
import getpass
from mpv import MPV
import sys

# === Configuración de paths dinámicos ===
USERNAME = getpass.getuser()
BASE_VIDEO_DIR = f"/home/{USERNAME}/Videos/videos_hd_final"
BASE_AUDIO_DIR = f"/home/{USERNAME}/Music"
ROLE_FILE = f"/home/{USERNAME}/device_role.txt"

# === Configuración de red ===
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"

# === Reproductor de audio independiente ===
mpv_audio = MPV()
mpv_audio.volume = 100

# === Estado global ===
leader_ip = None
categorias = []

# === Determinar carpeta según rol ===
def get_video_folder_by_role(role):
    if role == 'leader' or role == 'follower2':
        return "hor", "hor_text"
    elif role == 'follower1' or role == 'follower3':
        return "ver_rotated", "ver_rotated_text"
    else:
        print("⛔ Rol desconocido.")
        sys.exit(1)

# === Descubrimiento del líder por broadcast UDP ===
def discover_leader(timeout=30):
    global leader_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", BROADCAST_PORT))
    sock.settimeout(timeout)
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            if data.decode() == DISCOVERY_MESSAGE:
                leader_ip = addr[0]
                break
    except socket.timeout:
        print("⛔ No se detectó al líder.")
        sys.exit(1)
    finally:
        sock.close()
    return leader_ip

# === Registrar follower con el líder ===
def register_with_leader():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((leader_ip, FOLLOWER_PORT))
            hostname = socket.gethostname()
            s.sendall(f"REGISTER:{hostname}".encode('utf-8'))
        except Exception as e:
            print(f"❌ Error al registrar: {e}")
            sys.exit(1)

# === Reproducir audio independiente ===
def play_audio_background():
    try:
        audio_files = [f for f in os.listdir(BASE_AUDIO_DIR) if f.endswith(('.mp3', '.wav', '.ogg'))]
        if not audio_files:
            print("⚠️ No se encontraron audios.")
            return
        audio = random.choice(audio_files)
        mpv_audio.play(os.path.join(BASE_AUDIO_DIR, audio))
        mpv_audio.wait_for_playback()
    except Exception as e:
        print(f"⚠️ Error en audio: {e}")

# === Escuchar instrucciones del líder ===
def listen_for_commands(video_folder, text_folder):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', FOLLOWER_PORT))
    server.listen(1)
    while True:
        conn, _ = server.accept()
        data = conn.recv(1024).decode()
        if data.startswith("CATEGORIAS:"):
            global categorias
            categorias = data.split(":", 1)[1].split(",")
            print(f"🗂️ Categorías recibidas: {categorias}")
        elif data.startswith("PLAY:"):
            categoria = data.split(":", 1)[1]
            print(f"🎬 Reproduciendo categoría: {categoria}")
            play_category(categoria, video_folder, text_folder)
        elif data == "NEXT":
            continue

# === Elegir y reproducir 4 videos (3 normales + 1 texto) ===
def pick_videos(categoria, video_folder, text_folder):
    path = os.path.join(BASE_VIDEO_DIR, categoria, video_folder)
    text_path = os.path.join(BASE_VIDEO_DIR, categoria, text_folder)
    if not os.path.exists(path) or not os.path.exists(text_path):
        print(f"⚠️ Carpeta faltante en {categoria}")
        return []

    otros = [f for f in os.listdir(path) if f.endswith('.mp4')]
    textos = [f for f in os.listdir(text_path) if f.endswith('.mp4')]

    if len(otros) < 3 or len(textos) < 1:
        print(f"⚠️ No hay suficientes videos.")
        return []

    seleccionados = random.sample(otros, 3) + [random.choice(textos)]
    return [os.path.join(path, v) for v in seleccionados[:3]] + [os.path.join(text_path, seleccionados[3])]

# === Reproducir los videos de la categoría ===
def play_category(categoria, video_folder, text_folder):
    videos = pick_videos(categoria, video_folder, text_folder)
    if not videos:
        notify_done()
        return
    random.shuffle(videos)
    for v in videos:
        print(f"▶️ {os.path.basename(v)}")
        mpv = MPV()
        mpv.fullscreen = True
        mpv.hwdec = 'auto'
        mpv.play(v)
        mpv.wait_for_playback()
    notify_done()

# === Notificar finalización al líder ===
def notify_done():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((leader_ip, RESPONSE_PORT))
            s.sendall(b'done')
            print("✅ Notificación enviada al líder.")
        except Exception as e:
            print(f"❌ Error al notificar al líder: {e}")

# === Obtener rol desde archivo ===
def get_role():
    try:
        with open(ROLE_FILE, 'r') as f:
            return f.read().strip().lower()
    except:
        print("⛔ No se pudo leer el archivo de rol.")
        sys.exit(1)

# === Main ===
def main():
    role = get_role()
    if not role.startswith("follower"):
        print("⛔ Este dispositivo no es follower.")
        sys.exit(1)

    video_folder, text_folder = get_video_folder_by_role(role)

    print("🔍 Buscando al líder...")
    discover_leader()
    print(f"🎯 Líder detectado en: {leader_ip}")
    register_with_leader()

    threading.Thread(target=play_audio_background, daemon=True).start()
    listen_for_commands(video_folder, text_folder)

if __name__ == '__main__':
    main()
