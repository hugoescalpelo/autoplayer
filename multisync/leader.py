import socket
import os
import random
import threading
import time
from mpv import MPV

# === CONFIGURACIÓN ===
VIDEO_DIR = '/media/videos'
AUDIO_DIR = '/media/audios'
TEXT_INDICATOR = 'texto'
FOLLOWER_PORT = 9001
RESPONSE_PORT = 9100
BROADCAST_PORT = 8888
DISCOVERY_MESSAGE = "LEADER_HERE"

# === MPV para audio continuo ===
mpv_audio = MPV()
mpv_audio.volume = 100

# === Lista de followers activos ===
followers = set()
followers_lock = threading.Lock()

# === Función para enviar beacons por broadcast UDP ===
def broadcast_leader():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            sock.sendto(DISCOVERY_MESSAGE.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(2)
        except:
            break

# === Función para aceptar conexiones de followers ===
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

# === Esperar respuesta de finalización de videos ===
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

# === Reproducir audio continuo ===
def play_audio_background():
    audio = random.choice(os.listdir(AUDIO_DIR))
    mpv_audio.play(os.path.join(AUDIO_DIR, audio))
    mpv_audio.wait_for_playback()

# === Elegir categorías y videos ===
def pick_categories():
    return random.sample(os.listdir(VIDEO_DIR), k=len(os.listdir(VIDEO_DIR)))

def pick_videos(categoria):
    path = os.path.join(VIDEO_DIR, categoria)
    files = os.listdir(path)
    texto = [f for f in files if TEXT_INDICATOR in f]
    otros = [f for f in files if TEXT_INDICATOR not in f]
    return random.sample(otros, 3) + random.sample(texto, 1)

# === Enviar mensaje TCP a followers ===
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

# === Bucle principal del líder ===
def main():
    # Arrancar beacon y servidor de followers
    threading.Thread(target=broadcast_leader, daemon=True).start()
    threading.Thread(target=follower_server, daemon=True).start()
    threading.Thread(target=play_audio_background, daemon=True).start()

    print("Esperando a followers... (10s)")
    time.sleep(10)

    print("Iniciando sincronización.")
    categorias = pick_categories()
    send_to_followers("CATEGORIAS:" + ','.join(categorias))

    for cat in categorias:
        print(f"\n🔹 Categoría: {cat}")
        videos = pick_videos(cat)
        random.shuffle(videos)

        # Instrucción de reproducción
        send_to_followers("PLAY:" + cat)

        # Reproducir los videos en esta Raspberry
        for v in videos:
            mpv = MPV()
            mpv.fullscreen = True
            mpv.hwdec = 'auto'
            mpv.play(os.path.join(VIDEO_DIR, cat, v))
            mpv.wait_for_playback()

        # Esperar que followers terminen
        print("Esperando a que los followers terminen...")
        wait_for_completion(expected=len(followers))
        send_to_followers("NEXT")

    print("✅ Finalizado.")

if __name__ == '__main__':
    main()
