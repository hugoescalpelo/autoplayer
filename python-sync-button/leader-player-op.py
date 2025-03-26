import socket
import time
import subprocess
import json
import os
import glob
import re

VIDEO_DIR = "/home/pione/Videos"
SOCKET_PATH = "/tmp/mpvsocket"
SYNC_PORT = 5005

# Escaneo de videos por categoría y variante (A, B, C, etc.)
def scan_videos():
    pattern = re.compile(r"^(.*?)([A-Z])\.mp4$")
    library = {}
    for path in glob.glob(os.path.join(VIDEO_DIR, "*.mp4")):
        filename = os.path.basename(path)
        match = pattern.match(filename)
        if match:
            category, variant = match.groups()
            if category not in library:
                library[category] = []
            if variant not in library[category]:
                library[category].append(variant)
    return {cat: sorted(variants) for cat, variants in sorted(library.items())}

video_library = scan_videos()
categories = list(video_library.keys())

if not categories:
    print("No se encontraron videos.")
    exit(1)

category_index = [0]
variant_index = [0]
started = False

# Obtener nombre de video actual
def current_category():
    return categories[category_index[0]]

def current_variant():
    return video_library[current_category()][variant_index[0]]

def build_video_path():
    return os.path.join(VIDEO_DIR, f"{current_category()}{current_variant()}.mp4")

# Lanzar mpv con socket
def launch_mpv():
    subprocess.Popen([
        "mpv", build_video_path(),
        "--fs", "--no-terminal", "--loop",
        "--hwdec=drm",
        f"--input-ipc-server={SOCKET_PATH}"
    ])
    wait_for_socket()

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        time.sleep(0.1)

def send_mpv_command(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except:
        pass

def get_time_pos():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            return json.loads(response).get("data", 0)
    except:
        return 0

def get_pause():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "pause"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            return json.loads(response).get("data", False)
    except:
        return False

def reload_video():
    global started
    os.system("pkill mpv")
    time.sleep(0.5)
    launch_mpv()
    started = True

def switch_variant():
    variant_index[0] = (variant_index[0] + 1) % len(video_library[current_category()])
    reload_video()

def next_category():
    category_index[0] = (category_index[0] + 1) % len(categories)
    variant_index[0] = 0
    reload_video()

def prev_category():
    category_index[0] = (category_index[0] - 1) % len(categories)
    variant_index[0] = 0
    reload_video()

# Iniciar primer video
launch_mpv()

# Socket de sincronización con leader
sync_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sync_sock.bind(("", SYNC_PORT))
leader_ip = None
last_sync = 0

print("Esperando sincronización...")

while True:
    sync_sock.settimeout(0.2)
    try:
        data, addr = sync_sock.recvfrom(1024)
        leader_ip = addr[0]
        now = time.time()
        if now - last_sync > 9:
            leader_time = float(data.decode().strip())
            local_time = get_time_pos()
            offset = round(leader_time - local_time, 3)
            if not get_pause() and abs(offset) > 0.05:
                send_mpv_command({"command": ["set_property", "time-pos", leader_time]})
                print(f"Ajuste sincronización: desfase {offset:+.3f}s")
            last_sync = now
    except socket.timeout:
        pass

    # Escuchar cambios desde archivo de estado (opcional)
    # Podríamos implementar lectura de instrucciones desde otro archivo o método futuro
