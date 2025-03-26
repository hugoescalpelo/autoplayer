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

# Precompilar regex para A/B/C/etc.
pattern = re.compile(r"^(.*?)([A-Z])\.mp4$")

# Construir librería desde archivos .mp4
def build_library():
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

video_library = build_library()
categories = list(video_library.keys())

if not categories:
    print("❌ No se encontraron videos.")
    exit(1)

category_index = [0]
variant_index = [0]
started = False

# Utilidades
def current_category():
    return categories[category_index[0]]

def current_variant():
    return video_library[current_category()][variant_index[0]]

def build_video_path():
    return os.path.join(VIDEO_DIR, f"{current_category()}{current_variant()}.mp4")

def launch_mpv():
    subprocess.Popen([
        "mpv", build_video_path(),
        "--fs", "--no-terminal", "--loop",
        f"--input-ipc-server={SOCKET_PATH}"
    ])
    wait_for_socket()

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        time.sleep(0.1)

def send_mpv(command):
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

# Lanzar el primer video
launch_mpv()

# Sockets
sync_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sync_sock.bind(("", LISTEN_PORT))

control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_sock.bind(("127.0.0.1", CONTROL_PORT))

leader_ip = None
last_sync = 0

print("📡 Esperando sincronización...")

while True:
    sync_sock.settimeout(0.2)
    try:
        data, addr = sync_sock.recvfrom(1024)
        leader_ip = addr[0]
        now = time.time()
        if now - last_sync > 9:
            time_pos = float(data.decode().strip())
            local_pos = get_time_pos()
            offset = round(time_pos - local_pos, 3)
            if not get_pause() and abs(offset) > 0.05:
                send_mpv({"command": ["set_property", "time-pos", time_pos]})
                print(f"🔧 Ajuste: {offset:+.3f}s")
            last_sync = now
    except socket.timeout:
        pass

    control_sock.settimeout(0.1)
    try:
        cmd_data, _ = control_sock.recvfrom(1024)
        cmd = cmd_data.decode().strip()
        if cmd == "LOCAL_SWITCH_AB":
            switch_variant()
        elif cmd == "GLOBAL_NEXT_CATEGORY":
            next_category()
        elif cmd == "GLOBAL_PREV_CATEGORY":
            prev_category()
        elif cmd == "GLOBAL_TOGGLE_PLAY":
            send_mpv({"command": ["cycle", "pause"]})
        elif cmd == "GLOBAL_NEXT_5":
            t = get_time_pos()
            send_mpv({"command": ["set_property", "time-pos", t + 5]})
        elif cmd == "GLOBAL_PREV_5":
            t = get_time_pos()
            send_mpv({"command": ["set_property", "time-pos", max(0, t - 5)]})
    except socket.timeout:
        pass
