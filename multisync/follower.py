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
    VIDEO_SUBFOLDER = role_file.read().strip()

print(f"🎭 Follower iniciado con rol: {VIDEO_SUBFOLDER}")

LEADER_IP = None
CATEGORIAS = []
ultima_categoria = None
categoria_lock = threading.Lock()

# === Reproductor de espera invisible ===
def play_idle_loop():
    while not LEADER_IP:
        time.sleep(1)
    print("🕸️ En espera de instrucciones del líder...")

# === Escucha categoría y comandos del líder ===
def listen_commands():
    global ultima_categoria
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 9001))
    print("🎧 Escuchando comandos del líder en puerto 9001 UDP...")
    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode()
        if msg.startswith("CATEGORIAS:"):
            CATEGORIAS.clear()
            CATEGORIAS.extend(msg.split(":", 1)[1].split(","))
            print(f"📂 Categorías disponibles: {CATEGORIAS}")
        elif msg.startswith("PLAY:"):
            categoria = msg.split(":", 1)[1]
            print(f"🎬 Instrucción PLAY recibida: {categoria}")
            with categoria_lock:
                if categoria != ultima_categoria:
                    ultima_categoria = categoria
                    threading.Thread(target=reproduce_categoria, args=(categoria,), daemon=True).start()
        elif msg == "NEXT":
            print("➡️ Recibido NEXT")

# === Reproducir videos de categoría ===
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
        print("⚠️ No se encontraron videos para la categoría")
        return
    playlist = generate_playlist(videos)
    print(f"▶️ Reproduciendo videos: {videos}")
    subprocess.run([
        "mpv", "--fs", "--vo=gpu", "--hwdec=no", "--no-terminal", "--quiet",
        "--gapless-audio", "--image-display-duration=inf", "--no-stop-screensaver",
        "--keep-open=no", "--loop-playlist=no", f"--playlist={playlist}"
    ])
    os.remove(playlist)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(b'done', (LEADER_IP, 9100))
        print("✅ Señal DONE enviada al líder")
    except Exception as e:
        print(f"⚠️ Error al enviar DONE: {e}")

# === Audio ambiental continuo ===
def play_audio_background():
    files = [f for f in os.listdir(BASE_AUDIO_DIR) if f.lower().endswith(AUDIO_EXTENSIONS)]
    if not files:
        return
    file = random.choice(files)
    print(f"🔊 Reproduciendo audio ambiental: {file}")
    subprocess.Popen([
        "mpv", "--no-video", "--loop=no", "--quiet", "--no-terminal",
        os.path.join(BASE_AUDIO_DIR, file)
    ])

# === Buscar líder por broadcast ===
def discover_leader():
    global LEADER_IP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 8888))
    while not LEADER_IP:
        data, addr = sock.recvfrom(1024)
        if data.decode().startswith("LEADER_HERE"):
            LEADER_IP = addr[0]
            print(f"✅ Líder detectado en {LEADER_IP}")
            break

# === Registrar con el líder ===
def register_with_leader():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(f"REGISTER:{socket.gethostname()}".encode(), (LEADER_IP, 8899))
        print("📡 Registrado con el líder")
    except Exception as e:
        print(f"❌ Registro fallido: {e}")

# === MAIN ===
def main():
    threading.Thread(target=listen_commands, daemon=True).start()
    threading.Thread(target=play_idle_loop, daemon=True).start()
    discover_leader()
    register_with_leader()
    play_audio_background()
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
