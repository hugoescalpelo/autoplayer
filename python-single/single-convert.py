import os
import shutil
import subprocess
import json
import time
import socket
import glob
import re
from pathlib import Path
from gpiozero import Button
from signal import pause
from enum import IntEnum

# --- CONFIGURACIÓN GENERAL ---
USER = os.getenv("USER") or "pi"
VIDEO_DIR = Path(f"/home/{USER}/Videos")
SOCKET_PATH = "/tmp/mpvsocket"
PLAYLIST_FILE = VIDEO_DIR / "playlist.m3u"
USB_MOUNT_ROOT = Path("/media")
USB_FOLDER_NAME = "origins"
TEMP_DIR = Path("/tmp/converted_videos")

# --- GPIO ---
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.05)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.05)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.05)

# --- PARÁMETROS DE VIDEO ESPERADOS ---
EXPECTED_WIDTH = 1920
EXPECTED_HEIGHT = 1080
EXPECTED_FPS = 30
EXPECTED_BITRATE = 12000000
EXPECTED_CODEC = "h264"
EXPECTED_PROFILE = "High"
EXPECTED_LEVEL = "4.1"

# --- MODOS DE CONTROL ---
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2
    AB = 3

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# --- FUNCIONES DE OSD ---
def send_osd(msg):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            command = {"command": ["show-text", msg, 4000, 0]}
            client.send(json.dumps(command).encode() + b'\n')
    except:
        print(f"[OSD] {msg}")

def show_osd(title, button):
    mode = current_mode[0].name
    text = f"""
+-------------------------------+
| Modo: {mode:<10} Botón: {button:<8}|
+-------------------------------+

REPRO:  ←5s / →5s / Categorías
ROTAR:  Rotar 180°
ZOOM :  Zoom - / Zoom +
AB    :  Cambiar variante
"""
    send_osd(text)

# --- DETECCIÓN Y CONVERSIÓN ---
def find_usb_origins():
    USER = os.getenv("USER") or "pi"
    base_path = Path("/media") / USER

    if not base_path.exists():
        print(f"No existe la carpeta esperada: {base_path}")
        return None

    for device in base_path.iterdir():
        origins_path = device / "origins"
        if origins_path.exists() and origins_path.is_dir():
            print(f"Origen detectado: {origins_path}")
            return origins_path

    print("No se encontró carpeta 'origins' en ninguna USB montada.")
    return None

def is_valid_video(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
            capture_output=True,
            text=True
        )
        info = json.loads(result.stdout)
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                codec = stream.get("codec_name")
                profile = stream.get("profile")
                width = stream.get("width")
                height = stream.get("height")
                level = str(float(stream.get("level", 0)) / 10)
                fps = eval(stream.get("r_frame_rate", "0/1"))
                bitrate = int(stream.get("bit_rate", 0))
                return (
                    codec == EXPECTED_CODEC and profile == EXPECTED_PROFILE and level == EXPECTED_LEVEL and
                    width == EXPECTED_WIDTH and height == EXPECTED_HEIGHT and
                    round(fps) == EXPECTED_FPS and abs(bitrate - EXPECTED_BITRATE) <= 1000000
                )
    except:
        return False
    return False

def convert_to_valid_format(src, dst):
    if src.suffix.lower() == ".mp3":
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-f", "lavfi", "-i", "color=black:size=1920x1080:rate=30",
            "-i", str(src), "-shortest", "-c:v", "libx264", "-profile:v", "high",
            "-level:v", "4.1", "-b:v", "12M", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", str(dst)
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1",
            "-b:v", "12M", "-vf", "scale=1920:1080,fps=30", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", str(dst)
        ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def sync_and_convert_videos():
    usb_path = find_usb_origins()
    print(f"Path Memoria {usb_path}")
    if not usb_path:
        send_osd("No se detectó USB con carpeta /origins.")
        return False

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)

    send_osd("Sincronizando archivos...")

    for file in usb_path.glob("*"):
        if file.suffix.lower() not in [".mp4", ".mov", ".mp3"]:
            continue
        target = TEMP_DIR / (file.stem + ".mp4")

        if file.suffix.lower() == ".mp4" and is_valid_video(file):
            send_osd(f"Copiando {file.name}")
            shutil.copy(file, target)
        else:
            send_osd(f"Convirtiendo {file.name}")
            convert_to_valid_format(file, target)

    for f in VIDEO_DIR.glob("*.mp4"):
        f.unlink()
    for f in TEMP_DIR.glob("*.mp4"):
        shutil.copy(f, VIDEO_DIR)

    generate_playlist()
    send_osd("Videos actualizados correctamente.")
    return True

def generate_playlist():
    with open(PLAYLIST_FILE, "w") as f:
        for video in sorted(VIDEO_DIR.glob("*.mp4")):
            f.write(str(video) + "\n")

# --- PLAYLIST Y MPV ---
def build_playlist():
    pattern = re.compile(r"^(.*?)([A-Z])\.mp4$")
    files = sorted(glob.glob(str(VIDEO_DIR / "*.mp4")))
    playlist = []
    for f in files:
        name = os.path.basename(f)
        match = pattern.match(name)
        if match:
            category, variant = match.groups()
            playlist.append((category, variant, f))
    return playlist

playlist = build_playlist()
if not playlist:
    print("No se encontraron videos.")
    exit(1)

category_list = sorted(set(cat for cat, _, _ in playlist))
category_index = [0]
variant_index = [0]

def get_current_index():
    cat = category_list[category_index[0]]
    variants = [v for c, v, _ in playlist if c == cat]
    var = variants[variant_index[0] % len(variants)]
    for i, (c, v, _) in enumerate(playlist):
        if c == cat and v == var:
            return i
    return 0

def is_socket_available():
    return os.path.exists(SOCKET_PATH)

def send_mpv(command):
    if not is_socket_available():
        return
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except:
        pass

# --- FUNCIONES DE REPRODUCCIÓN ---
def toggle_pause():
    send_mpv({"command": ["cycle", "pause"]})

def seek(offset):
    send_mpv({"command": ["add", "time-pos", offset]})

def rotate_180():
    send_mpv({"command": ["cycle-values", "video-rotate", "0", "180"]})

def zoom_in():
    if zoom_level[0] < 1.0:
        zoom_level[0] += 0.05
        send_mpv({"command": ["set_property", "video-zoom", round(zoom_level[0], 2)]})

def zoom_out():
    if zoom_level[0] > -1.0:
        zoom_level[0] -= 0.05
        send_mpv({"command": ["set_property", "video-zoom", round(zoom_level[0], 2)]})

def switch_ab():
    variant_index[0] += 1
    jump_to_current()

def next_category():
    category_index[0] = (category_index[0] + 1) % len(category_list)
    variant_index[0] = 0
    jump_to_current()

def prev_category():
    category_index[0] = (category_index[0] - 1) % len(category_list)
    variant_index[0] = 0
    jump_to_current()

def jump_to_current():
    idx = get_current_index()
    send_mpv({"command": ["playlist-play-index", idx]})
    send_osd(f"Video: {playlist[idx][0]}{playlist[idx][1]}")

# --- CONTROL DE BOTONES ---
def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))

def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

def handle_menu():
    duration = hold_duration(BTN_MENU)
    show_osd("Menú", "MENU")
    if duration < 0.5 and current_mode[0] == Mode.REPRO:
        toggle_pause()
    elif duration >= 0.5:
        cycle_mode()

def handle_left():
    duration = hold_duration(BTN_LEFT)
    show_osd("Acción", "IZQUIERDA")
    mode = current_mode[0]
    if mode == Mode.REPRO:
        if duration < 0.5:
            seek(-5)
        else:
            prev_category()
    elif mode == Mode.ROTAR:
        rotate_180()
    elif mode == Mode.ZOOM:
        zoom_out()
    elif mode == Mode.AB:
        switch_ab()

def handle_right():
    duration = hold_duration(BTN_RIGHT)
    show_osd("Acción", "DERECHA")
    mode = current_mode[0]
    if mode == Mode.REPRO:
        if duration < 0.5:
            seek(5)
        else:
            next_category()
    elif mode == Mode.ROTAR:
        rotate_180()
    elif mode == Mode.ZOOM:
        zoom_in()
    elif mode == Mode.AB:
        switch_ab()

# --- INICIO DE MPV Y PROGRAMA ---
def wait_for_socket():
    for _ in range(20):
        if SOCKET_PATH and Path(SOCKET_PATH).exists():
            return True
        time.sleep(1)
    return False

BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

subprocess.Popen([
    "mpv", "--fs", "--loop-playlist", "--no-terminal", "--no-osd-bar",
    "--osd-level=1", "--hwdec=drm", "--vo=gpu",
    f"--input-ipc-server={SOCKET_PATH}",
    "--osd-font='Liberation Mono'",
    "--osd-font-size=26",
    "--playlist", str(PLAYLIST_FILE)
])

if wait_for_socket():
    sync_and_convert_videos()
else:
    print("No se pudo iniciar el socket de MPV.")

pause()
