from gpiozero import Button
from signal import pause
import time
import socket
import json
import os
import shutil
import subprocess
import glob
import re
from enum import IntEnum
from pathlib import Path

# --- CONFIGURACIÓN ---
USER = os.getenv("USER") or "pi"
VIDEO_DIR = Path(f"/home/{USER}/Videos")
SOCKET_PATH = "/tmp/mpvsocket"
USB_MOUNT_ROOT = Path("/media") / USER
USB_FOLDER_NAME = "origins"
PLAYLIST_FILE = VIDEO_DIR / "playlist.m3u"

# --- GPIO ---
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.05)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.05)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.05)

# --- MODOS ---
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# --- FUNCIONES MPV ---
def is_socket_available():
    return os.path.exists(SOCKET_PATH)

def send_mpv(command):
    if not is_socket_available():
        return
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except (BrokenPipeError, ConnectionRefusedError):
        print("Socket roto o inaccesible.")

def send_osd(msg):
    send_mpv({"command": ["show-text", msg, 4000, 0]})

# --- OSD DETALLADO ---
def show_osd(title, button):
    if not is_socket_available():
        return
    mode = current_mode[0].name
    text = f"""
+-----------------------------------+
| Modo actual: {mode:<12}         |
| Botón presionado: {button:<8}        |
+-----------------------------------+

Funciones del modo:
  -> : {get_action_description(mode, 'left')}
  <- : {get_action_description(mode, 'right')}

Modos disponibles:
  REPRO  : reproducir y navegar
  ROTAR  : rotación de imagen
  ZOOM   : acercar/alejar
"""
    send_osd(text)

def get_action_description(mode, button):
    if mode == "REPRO":
        if button == "left":
            return "←5s"
        elif button == "right":
            return "→5s"
        elif button == "menu":
            return "Pausa/Reanudar"
    elif mode == "ROTAR":
        return "Rotar 180°"
    elif mode == "ZOOM":
        return "Zoom -5%" if button == "left" else "Zoom +5%"
    return "-"

# --- ACCIONES ---
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

def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))

def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

# --- HANDLERS ---
def handle_menu():
    duration = hold_duration(BTN_MENU)
    show_osd("Menu", "MENU")
    if duration < 0.5 and current_mode[0] == Mode.REPRO:
        toggle_pause()
    elif duration >= 0.5:
        cycle_mode()

def handle_left():
    duration = hold_duration(BTN_LEFT)
    show_osd("Izquierda", "LEFT")
    if current_mode[0] == Mode.REPRO:
        seek(-5)
    elif current_mode[0] == Mode.ROTAR:
        rotate_180()
    elif current_mode[0] == Mode.ZOOM:
        zoom_out()

def handle_right():
    duration = hold_duration(BTN_RIGHT)
    show_osd("Derecha", "RIGHT")
    if current_mode[0] == Mode.REPRO:
        seek(5)
    elif current_mode[0] == Mode.ROTAR:
        rotate_180()
    elif current_mode[0] == Mode.ZOOM:
        zoom_in()

# --- REPRODUCCIÓN MPV ---
def launch_mpv():
    files = list(VIDEO_DIR.glob("*.mp4")) + list(VIDEO_DIR.glob("*.mov"))
    if not files:
        print("No se encontraron videos para reproducir.")
        return
    os.system("pkill mpv")
    time.sleep(1)
    os.system(
        f"mpv {' '.join(map(str, files))} "
        f"--fs --loop-playlist --no-config --no-osd-bar --osd-level=1 "
        f"--vo=gpu --hwdec=drm "
        f"--osd-font-size=26 --osd-font='Liberation Mono' "
        f"--input-ipc-server={SOCKET_PATH} &"
    )

# --- SINCRONIZACIÓN DE VIDEOS ---
def find_usb_origins():
    base_path = USB_MOUNT_ROOT
    if not base_path.exists():
        return None
    for device in base_path.iterdir():
        path = device / USB_FOLDER_NAME
        if path.exists() and path.is_dir():
            return path
    return None

def generate_playlist():
    with open(PLAYLIST_FILE, "w") as f:
        for video in sorted(VIDEO_DIR.glob("*.mp4")) + sorted(VIDEO_DIR.glob("*.mov")):
            f.write(str(video) + "\n")

def sync_videos():
    usb_path = find_usb_origins()
    if not usb_path:
        send_osd("No se detectó USB con carpeta 'origins'.")
        return False
    send_osd("USB detectada. Iniciando copia...")
    for f in VIDEO_DIR.glob("*.mp4"):
        f.unlink()
    for f in VIDEO_DIR.glob("*.mov"):
        f.unlink()
    for file in usb_path.glob("*"):
        if file.suffix.lower() in [".mp4", ".mov"]:
            shutil.copy(file, VIDEO_DIR)
    generate_playlist()
    send_osd("Copia completada.")
    return True

# --- INICIAR SISTEMA ---
BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

launch_mpv()
time.sleep(2)
sync_videos()
pause()
