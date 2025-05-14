import socket
import os
import random
import threading
import time
from mpv import MPV
import sys

# === CONFIGURACIÓN ===
VIDEO_DIR = '/media/videos'
AUDIO_DIR = '/media/audios'
TEXT_INDICATOR = 'texto'
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"
ROLE_FILE = '/home/pi/device_role.txt'

# === Variables globales ===
leader_ip = None
categorias = []

# === MPV para audio ===
mpv_audio = MPV()
mpv_audio.volume = 100

# === Función para descubrir líder por UDP ===
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
        print("⛔ Tiempo de espera agotado sin encontrar al líder.")
        sys.exit(1)
    finally:
        sock.close()
    return leader_ip

# === Función para registrar este follower con el líder ===
def register_with_leader():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((leader_ip, FOLLOWER_PORT))
            hostname = socket.gethostname()
            s.sendall(f"REGISTER:{hostname}".encode('utf-8'))
        except Exception as e:
            print(f"❌ Error al registrar con el líder: {e}")
            sys.exit(1)

# === Reproducir audio independiente ===
def play_audio_background():
    try:
        audio = random.choice(os.listdir(AUDIO_DIR))
        mpv_audio.play(os.path.join(AUDIO_DIR, audio))
        mpv_audio.wait_for_playback()
    except Exception as e:
        print(f"⚠️ Error al reproducir audio: {e}")

# === Escuchar instrucciones del líder ===
def listen_for_commands():
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
            play_category(categoria)
        elif data == "NEXT":
            continue

# === Elegir y reproducir 4 videos (uno con texto) ===
def pick_videos(categoria):
    path = os.path.join(VIDEO_DIR, categoria)
    files = os.listdir(path)
    texto = [f for f in files if TEXT_INDICATOR in f]
    otros = [f for f in files if TEXT_INDICATOR not in f]
    if len(texto) < 1 or len(otros) < 3:
        print(f"❗ No hay suficientes videos en {categoria}")
        return []
    return random.sample(otros, 3) + random.sample(texto, 1)

def play_category(categoria):
    videos = pick_videos(categoria)
    if not videos:
        notify_done()
        return
    random.shuffle(videos)
    for v in videos:
        print(f"▶️ {v}")
        mpv = MPV()
        mpv.fullscreen = True
        mpv.hwdec = 'auto'
        mpv.play(os.path.join(VIDEO_DIR, categoria, v))
        mpv.wait_for_playback()
    notify_done()

# === Enviar confirmación al líder ===
def notify_done():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((leader_ip, RESPONSE_PORT))
            s.sendall(b'done')
            print("✅ Reproducción completada. Notificado al líder.")
        except Exception as e:
            print(f"❌ No se pudo notificar al líder: {e}")

# === Obtener rol del archivo ===
def get_role():
    try:
        with open(ROLE_FILE, 'r') as f:
            return f.read().strip().lower()
    except:
        return "unknown"

# === Main ===
def main():
    role = get_role()
    if not role.startswith("follower"):
        print("⛔ Este dispositivo no está configurado como follower.")
        sys.exit(1)

    print("🔍 Buscando al líder...")
    discover_leader()
    print(f"🎯 Líder encontrado en: {leader_ip}")

    register_with_leader()
    threading.Thread(target=play_audio_background, daemon=True).start()
    listen_for_commands()

if __name__ == '__main__':
    main()
