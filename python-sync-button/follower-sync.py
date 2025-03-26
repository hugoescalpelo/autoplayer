import socket
import time
import subprocess
import json
import os
import glob
import re

VIDEO_DIR = "/home/pitwo/Videos"
SOCKET_PATH = "/tmp/mpvsocket"
LISTEN_PORT = 5005
CONTROL_PORT = 5007

# Escanear videos
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

    return {cat: sorted(variants) for cat, variants in sorted(library.items())}

video_library = scan_video_library()
categories = list(video_library.keys())

if not categories:
    print("❌ No se encontraron videos válidos.")
    exit(1)

category_index = [0]
variant_index = [0]

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
        f"--input-ipc-server={SOCKET_PATH}",
        "--pause"
    ])

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

def send_mpv_command(command):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps(command).encode() + b'\n')
        client.close()
    except Exception as e:
        print(f"⚠️ Error enviando a mpv: {e}")

def reload_video():
    os.system("pkill mpv")
    time.sleep(1)
    launch_mpv()
    wait_for_socket()

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
sync_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sync_sock.bind(("", LISTEN_PORT))

local_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
local_sock.bind(("127.0.0.1", CONTROL_PORT))

leader_ip = None
last_sync_time = 0

print("📡 Esperando sincronización del leader...")

# Loop principal
while True:
    # Sincronización desde leader
    sync_sock.settimeout(1)
    try:
        data, addr = sync_sock.recvfrom(1024)
        if leader_ip is None:
            leader_ip = addr[0]
            print(f"🌐 Leader detectado en: {leader_ip}")

        now = time.time()
        if now - last_sync_time >= 10:
            time_pos = float(data.decode().strip())
            send_mpv_command({"command": ["set_property", "time-pos", time_pos]})
            send_mpv_command({"command": ["set_property", "pause", False]})
            last_sync_time = now
    except socket.timeout:
        pass

    # Control local
    local_sock.settimeout(0.1)
    try:
        data, _ = local_sock.recvfrom(1024)
        cmd = data.decode().strip()
        if cmd == "LOCAL_SWITCH_VARIANT":
            switch_variant()
        elif cmd == "GLOBAL_NEXT_CATEGORY":
            next_category()
        elif cmd == "GLOBAL_PREV_CATEGORY":
            prev_category()
    except socket.timeout:
        pass
