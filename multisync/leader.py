import socket
import os
import random
import threading
import time
from mpv import MPV
from pathlib import Path
import getpass

# === Configuración dinámica de paths ===
USERNAME = getpass.getuser()
BASE_VIDEO_DIR = f"/home/{USERNAME}/Videos/videos_hd_final"
BASE_AUDIO_DIR = f"/home/{USERNAME}/Music"

VIDEO_SUBFOLDER = "hor"  # Este líder reproduce videos horizontales
TEXT_SUFFIX = "_text"
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"

# === Extensiones soportadas ===
VIDEO_EXTENSIONS = ('.mp4', '.mov')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg')

# === MPV para audio continuo ===
mpv_audio = MPV()
mpv_audio.volume = 100

# === Seguimiento de followers ===
followers = set()
followers_lock = threading.Lock()

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
            print(f"Mensaje inesperado de {addr}: {data}")

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

def play_audio_background():
    try:
        audio_files = [f for f in os.listdir(BASE_AUDIO_DIR) if f.lower().endswith(AUDIO_EXTENSIONS)]
        if not audio_files:
            print("⚠️ No se encontraron audios.")
            return
        audio = random.choice(audio_files)
        mpv_audio.play(os.path.join(BASE_AUDIO_DIR, audio))
        mpv_audio.wait_for_playback()
    except Exception as e:
        print(f"Error al reproducir audio: {e}")

def pick_categories():
    return [d for d in os.listdir(BASE_VIDEO_DIR)
            if os.path.isdir(os.path.join(BASE_VIDEO_DIR, d))]

def pick_videos(categoria):
    path = os.path.join(BASE_VIDEO_DIR, categoria, VIDEO_SUBFOLDER)
    text_path = os.path.join(BASE_VIDEO_DIR, categoria, f"{VIDEO_SUBFOLDER}_text")
    if not os.path.exists(path) or not os.path.exists(text_path):
        print(f"⚠️ Carpeta faltante en categoría {categoria}")
        return []
    
    otros = [f for f in os.listdir(path) if f.lower().endswith(VIDEO_EXTENSIONS)]
    textos = [f for f in os.listdir(text_path) if f.lower().endswith(VIDEO_EXTENSIONS)]

    if len(otros) < 3 or len(textos) < 1:
        print(f"⚠️ No hay suficientes videos en {categoria}")
        return []

    seleccionados = random.sample(otros, 3) + [random.choice(textos)]
    return [os.path.join(path, v) for v in seleccionados[:3]] + [os.path.join(text_path, seleccionados[3])]

def send_to_followers(message):
    with followers_lock:
        for host in list(followers):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, FOLLOWER_PORT))
                    s.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Error al enviar a {host}: {e}")
                followers.remove(host)

def main():
    threading.Thread(target=broadcast_leader, daemon=True).start()
    threading.Thread(target=follower_server, daemon=True).start()
    threading.Thread(target=play_audio_background, daemon=True).start()

    print("🔄 Esperando a followers... (10s)")
    time.sleep(10)

    categorias = pick_categories()
    if not categorias:
        print("❌ No se encontraron categorías.")
        return

    random.shuffle(categorias)
    send_to_followers("CATEGORIAS:" + ','.join(categorias))

    for cat in categorias:
        print(f"\n🎬 Categoría actual: {cat}")
        videos = pick_videos(cat)
        if not videos:
            print("⚠️ No se pudieron cargar los videos de esta categoría.")
            continue

        send_to_followers("PLAY:" + cat)

        for v in videos:
            print(f"▶️ Reproduciendo: {os.path.basename(v)}")
            mpv = MPV()
            mpv.fullscreen = True
            mpv.hwdec = 'auto'
            mpv.play(v)
            mpv.wait_for_playback()

        print("⏳ Esperando a followers...")
        wait_for_completion(expected=len(followers))
        send_to_followers("NEXT")

    print("\n✅ Todas las categorías reproducidas. Fin del ciclo.")

if __name__ == '__main__':
    main()
