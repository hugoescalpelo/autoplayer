import socket
import json
import time
import os
import glob
import re

VIDEO_DIR = "/home/pitwo/Videos"
SOCKET_PATH = "/tmp/mpvsocket"
UDP_PORT = 5007

# --- Utilidades para mpv ---
def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

def send_mpv_command(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except Exception as e:
        print(f"⚠️ Error enviando comando a mpv: {e}")

# --- Escanear y organizar videos por categoría y variante ---
def scan_video_library():
    pattern = re.compile(r"^(.*?)([A-Z])\.mp4$", re.IGNORECASE)
    library = {}

    for path in glob.glob(os.path.join(VIDEO_DIR, "*.mp4")):
        filename = os.path.basename(path)
        match = pattern.match(filename)
        if match:
            category, variant = match.groups()
            category = category.strip()
            variant = variant.upper()
            if category not in library:
                library[category] = []
            if variant not in library[category]:
                library[category].append(variant)

    return {cat: sorted(variants) for cat, variants in sorted(library.items())}

video_library = scan_video_library()
categories = list(video_library.keys())

category_index = [0]
variant_index = [0]
current_video_path = [None]

def current_category():
    return categories[category_index[0]]

def current_variant():
    return video_library[current_category()][variant_index[0]]

def build_video_path():
    return os.path.join(VIDEO_DIR, f"{current_category()}{current_variant()}.mp4")

def load_current_video():
    new_path = build_video_path()
    if current_video_path[0] != new_path:
        print(f"🎬 Reproduciendo: {new_path}")
        send_mpv_command({"command": ["loadfile", new_path, "replace"]})
        current_video_path[0] = new_path
    else:
        print("⏭️ Video ya cargado, no se recarga.")

# --- Acciones de control ---
def switch_variant():
    variants = video_library[current_category()]
    variant_index[0] = (variant_index[0] + 1) % len(variants)
    load_current_video()

def next_category():
    category_index[0] = (category_index[0] + 1) % len(categories)
    variant_index[0] = 0
    load_current_video()

def prev_category():
    category_index[0] = (category_index[0] - 1) % len(categories)
    variant_index[0] = 0
    load_current_video()

def rotate_180():
    send_mpv_command({"command": ["cycle-values", "video-rotate", "0", "180"]})

def zoom_in():
    send_mpv_command({"command": ["multiply", "video-zoom", 1.05]})

def zoom_out():
    send_mpv_command({"command": ["multiply", "video-zoom", 0.95]})

def toggle_pause():
    send_mpv_command({"command": ["cycle", "pause"]})

def seek_forward():
    send_mpv_command({"command": ["add", "time-pos", 5]})

def seek_backward():
    send_mpv_command({"command": ["add", "time-pos", -5]})

# --- Diccionario de comandos ---
commands = {
    "LOCAL_ROTATE_180": rotate_180,
    "LOCAL_ZOOM_IN": zoom_in,
    "LOCAL_ZOOM_OUT": zoom_out,
    "LOCAL_SWITCH_AB": switch_variant,
    "GLOBAL_TOGGLE_PLAY": toggle_pause,
    "GLOBAL_NEXT_5": seek_forward,
    "GLOBAL_PREV_5": seek_backward,
    "GLOBAL_NEXT_CATEGORY": next_category,
    "GLOBAL_PREV_CATEGORY": prev_category
}

# --- Inicialización ---
wait_for_socket()
load_current_video()

# --- Servidor UDP local ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", UDP_PORT))
print("📡 Receptor follower optimizado en espera...")

while True:
    try:
        data, _ = sock.recvfrom(1024)
        cmd = data.decode().strip()
        print(f"🎮 Comando recibido: {cmd}")
        if cmd in commands:
            commands[cmd]()
        else:
            print(f"❓ Comando no reconocido: {cmd}")
    except Exception as e:
        print(f"❌ Error en receptor: {e}")
        time.sleep(0.5)
