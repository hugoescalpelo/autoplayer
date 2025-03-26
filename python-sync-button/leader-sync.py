import socket
import time
import subprocess
import json
import os
import glob
import re

VIDEO_DIR = "/home/pione/Videos"
SOCKET_PATH = "/tmp/mpvsocket"
BROADCAST_IP = "255.255.255.255"
SYNC_PORT = 5005
CONTROL_PORT = 5007

# Escanear biblioteca
def scan_video_library():
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
    print(f"Bilbioteca de Video {video_library}")
    return {cat: sorted(variants) for cat, variants in sorted(library.items())}

video_library = scan_video_library()
categories = list(video_library.keys())

if not categories:
    print("❌ No se encontraron videos válidos.")
    exit(1)

category_index = [0]
variant_index = [0]
pause_state = False

def current_category():
    return categories[category_index[0]]

def current_variant():
    return video_library[current_category()][variant_index[0]]

def build_video_path():
    return os.path.join(VIDEO_DIR, f"{current_category()}{current_variant()}.mp4")

def launch_mpv():
    print(f"🎬 Reproduciendo: {build_video_path()}")
    subprocess.Popen([
        "mpv", build_video_path(),
        "--fs", "--no-terminal", "--loop",
        f"--input-ipc-server={SOCKET_PATH}"
    ])

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

def get_time_pos():
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
        response = client.recv(1024).decode()
        client.close()
        return json.loads(response).get("data", 0)
    except Exception as e:
        print(f"⚠️ Error obteniendo tiempo: {e}")
        return 0

def get_pause_state():
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps({"command": ["get_property", "pause"]}).encode() + b'\n')
        response = client.recv(1024).decode()
        client.close()
        return json.loads(response).get("data", False)
    except:
        return False

def reload_video():
    global pause_state
    pause_state = get_pause_state()
    os.system("pkill mpv")
    time.sleep(1)
    launch_mpv()
    wait_for_socket()
    if pause_state:
        send_mpv_command({"command": ["set_property", "pause", True]})

def send_mpv_command(command):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps(command).encode() + b'\n')
        client.close()
    except:
        pass

def switch_variant():
    variants = video_library[current_category()]
    variant_index[0] = (variant_index[0] + 1) % len(variants)
    print(f"🔁 Cambiando a variante: {current_variant()}")
    reload_video()

def next_category():
    category_index[0] = (category_index[0] + 1) % len(categories)
    variant_index[0] = 0
    print(f"➡️ Siguiente categoría: {current_category()}")
    reload_video()

def prev_category():
    category_index[0] = (category_index[0] - 1) % len(categories)
    variant_index[0] = 0
    print(f"⬅️ Categoría anterior: {current_category()}")
    reload_video()

# Iniciar
launch_mpv()
wait_for_socket()

# Sockets
control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_sock.bind(("127.0.0.1", CONTROL_PORT))

broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

print("📡 Leader emitiendo sincronización cada 10 segundos y escuchando control...")

last_sync = time.time()

while True:
    # Sincronizar cada 10 segundos
    if time.time() - last_sync >= 10:
        current_time = get_time_pos()
        broadcast_sock.sendto(str(current_time).encode(), (BROADCAST_IP, SYNC_PORT))
        last_sync = time.time()

    # Recibir comandos
    control_sock.settimeout(0.1)
    try:
        data, _ = control_sock.recvfrom(1024)
        cmd = data.decode().strip()
        if cmd == "LOCAL_SWITCH_VARIANT":
            switch_variant()
        elif cmd == "GLOBAL_NEXT_CATEGORY":
            next_category()
        elif cmd == "GLOBAL_PREV_CATEGORY":
            prev_category()
    except socket.timeout:
        pass
