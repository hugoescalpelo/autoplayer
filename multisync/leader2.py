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
BASE_AUDIO_DIR = f"/home/{USERNAME}/Music/audios"
VIDEO_SUBFOLDERS = ["ver", "ver_text"]  # Leader solo reproduce contenido vertical
VIDEO_EXTENSIONS = ('.mp4', '.mov')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg')

followers = set()
categoria_queue = []
done_flag = threading.Event()
current_category = None

# === Broadcast periódico del líder con la categoría actual ===
def broadcast_leader():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        msg = f"LEADER_HERE:{','.join(categoria_queue)}"
        sock.sendto(msg.encode(), ('<broadcast>', 8888))
        if current_category:
            sock.sendto(f"PLAY:{current_category}".encode(), ('<broadcast>', 9001))
        time.sleep(2)  # emisión frecuente para mantener sincronía

# === Escuchar registros de nuevos followers ===
def listen_for_followers():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 8899))
    print("👂 Esperando registros de followers en puerto 8899 UDP...")
    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode()
        if msg.startswith("REGISTER:"):
            followers.add(addr[0])
            print(f"✅ Nuevo follower registrado desde {addr[0]}")

# === Enviar comandos a todos los followers ===
def send_to_followers(message):
    for ip in list(followers):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(message.encode(), (ip, 9001))
            print(f"📨 Enviado a {ip}: {message}")
        except Exception as e:
            print(f"⚠️ Error al enviar a {ip}: {e}")
            followers.discard(ip)

# === Recibir notificaciones DONE ===
def receive_done():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 9100))
    print("🕓 Esperando señales DONE en puerto 9100 UDP...")
    while True:
        data, addr = sock.recvfrom(1024)
        if data.decode() == 'done':
            print(f"✔️ DONE recibido de {addr[0]}")
            done_flag.set()

# === Utilidades para manejo de videos ===
def is_valid_video(filename):
    return filename.lower().endswith(VIDEO_EXTENSIONS)

def is_valid_audio(filename):
    return filename.lower().endswith(AUDIO_EXTENSIONS)

def pick_categories():
    return [d for d in os.listdir(BASE_VIDEO_DIR)
            if os.path.isdir(os.path.join(BASE_VIDEO_DIR, d))]

def pick_videos(categoria):
    blocks = []
    for subfolder in VIDEO_SUBFOLDERS:
        path = os.path.join(BASE_VIDEO_DIR, categoria, subfolder)
        if not os.path.exists(path):
            continue
        files = [f for f in os.listdir(path) if is_valid_video(f)]
        if files:
            sample = random.sample(files, min(len(files), 4))
            blocks.append([os.path.join(path, f) for f in sample])
    return blocks

def generate_playlist(blocks):
    f = NamedTemporaryFile(delete=False, mode='w', suffix=".m3u")
    for block in blocks:
        for video in block:
            f.write(video + '\n')
    f.close()
    return f.name

def play_video_sequence(playlist_path):
    subprocess.run([
        "mpv", "--fs", "--vo=gpu", "--hwdec=no", "--no-terminal", "--quiet",
        "--gapless-audio", "--image-display-duration=inf", "--no-stop-screensaver",
        "--keep-open=no", "--loop-playlist=no", f"--playlist={playlist_path}"
    ])
    os.remove(playlist_path)

def play_loop():
    global current_category
    for categoria in categoria_queue:
        print(f"🎬 Reproduciendo categoría: {categoria}")
        current_category = categoria
        blocks = pick_videos(categoria)
        if not blocks:
            print(f"⚠️ No se encontraron videos para {categoria}")
            continue
        playlist = generate_playlist(blocks)
        threading.Thread(target=send_done_later, daemon=True).start()
        play_video_sequence(playlist)
        print("⏳ Esperando DONE de cualquier follower...")
        done_flag.wait()
        send_to_followers("NEXT")
        done_flag.clear()

def send_done_later():
    time.sleep(2)
    done_flag.set()

def play_audio_background():
    audio_files = [f for f in os.listdir(BASE_AUDIO_DIR) if is_valid_audio(f)]
    if audio_files:
        audio = random.choice(audio_files)
        subprocess.Popen([
            "mpv", "--no-video", "--loop=no", "--quiet",
            "--no-terminal", os.path.join(BASE_AUDIO_DIR, audio)
        ])

# === MAIN ===
def main():
    global categoria_queue
    categoria_queue = pick_categories()
    print(f"🎞️ Plan de reproducción: {categoria_queue}")
    threading.Thread(target=broadcast_leader, daemon=True).start()
    threading.Thread(target=listen_for_followers, daemon=True).start()
    threading.Thread(target=receive_done, daemon=True).start()
    play_audio_background()
    while True:
        random.shuffle(categoria_queue)
        play_loop()

if __name__ == '__main__':
    main()
