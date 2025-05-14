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

VIDEO_EXTENSIONS = ('.mp4', '.mov')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.ogg')

with open(f"/home/{USERNAME}/role.txt", "r") as role_file:
    VIDEO_SUBFOLDER = role_file.read().strip()  # cada follower define su carpeta por FOLLOWER_ID
LEADER_IP = None
CATEGORIAS = []
NEXT_EVENT = threading.Event()

# === Comunicación con líder ===
def discover_leader():
    global LEADER_IP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 8888))
    while True:
        data, addr = sock.recvfrom(1024)
        if data.decode().strip() == "LEADER_HERE":
            LEADER_IP = addr[0]
            break

# === Registro como follower ===
def register_with_leader():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LEADER_IP, 9001))
            s.sendall(f"REGISTER:{socket.gethostname()}".encode())
    except:
        print("❌ No se pudo registrar con el líder")

# === Receptor de órdenes ===
def listen_commands():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 9001))
    server.listen(5)
    while True:
        conn, _ = server.accept()
        data = conn.recv(1024).decode()
        if data.startswith("CATEGORIAS:"):
            categorias_str = data.split(":", 1)[1]
            CATEGORIAS.clear()
            CATEGORIAS.extend(categorias_str.split(","))
        elif data.startswith("PLAY:"):
            categoria = data.split(":", 1)[1]
            threading.Thread(target=reproduce_categoria, args=(categoria,), daemon=True).start()
        elif data == "NEXT":
            NEXT_EVENT.set()

# === Reproducción de 4 videos como playlist ===
def pick_videos(categoria):
    path = os.path.join(BASE_VIDEO_DIR, categoria, VIDEO_SUBFOLDER)
    text_path = os.path.join(BASE_VIDEO_DIR, categoria, f"{VIDEO_SUBFOLDER}_text")
    if not os.path.exists(path) or not os.path.exists(text_path):
        return []
    otros = [f for f in os.listdir(path) if f.lower().endswith(VIDEO_EXTENSIONS)]
    textos = [f for f in os.listdir(text_path) if f.lower().endswith(VIDEO_EXTENSIONS)]
    if len(otros) >= 3 and len(textos) >= 1:
        texto = random.choice(textos)
        normales = random.sample(otros, 3)
        return [os.path.join(text_path, texto)] + [os.path.join(path, f) for f in normales]
    return []

def generate_playlist(videos):
    f = NamedTemporaryFile(delete=False, mode='w', suffix=".m3u")
    for v in videos:
        f.write(v + '\n')
    f.close()
    return f.name

def reproduce_categoria(categoria):
    videos = pick_videos(categoria)
    if not videos:
        return
    playlist = generate_playlist(videos)
    subprocess.run([
        "mpv", "--fs", "--vo=gpu", "--hwdec=no", "--no-terminal", "--quiet",
        "--gapless-audio", "--image-display-duration=inf", "--no-stop-screensaver",
        "--keep-open=no", "--loop-playlist=no", f"--playlist={playlist}"
    ])
    os.remove(playlist)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LEADER_IP, 9100))
            s.sendall(b'done')
    except:
        print("⚠️ No se pudo enviar DONE al líder")

# === Audio ambiental continuo ===
def play_audio_background():
    files = [f for f in os.listdir(BASE_AUDIO_DIR) if f.lower().endswith(AUDIO_EXTENSIONS)]
    if not files:
        return
    file = random.choice(files)
    subprocess.Popen([
        "mpv", "--no-video", "--loop=no", "--quiet", "--no-terminal",
        os.path.join(BASE_AUDIO_DIR, file)
    ])

# === MAIN ===
def main():
    discover_leader()
    register_with_leader()
    threading.Thread(target=listen_commands, daemon=True).start()
    play_audio_background()
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
