from gpiozero import Button
from signal import pause
import time
import socket
import json
import os
import glob
import subprocess
import shutil
from pathlib import Path
from enum import IntEnum

# --- CONFIGURACIÓN ---
USER = os.getenv("USER") or "pi"
VIDEO_DIR = Path(f"/home/{USER}/Videos")
USB_MOUNT_ROOT = Path("/media") / USER
USB_FOLDER_NAME = "origins"
SOCKET_PATH = "/tmp/mpvsocket"
PLAYLIST_FILE = VIDEO_DIR / "playlist.m3u"

# GPIO
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.05)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.05)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.05)

# Modos
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# Mostrar texto en mpv

def send_mpv(command):
    if not os.path.exists(SOCKET_PATH):
        return
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except:
        pass

def show_osd(title, button):
    mode = current_mode[0].name
    text = f"""
+-----------------------------------+
| Modo actual: {mode:<12}         |
| Botón presionado: {button:<8}        |
+-----------------------------------+

😎😎😎 Funciones del modo 😎😎😎
  -> : {get_action_description(mode, 'right')}
  <- : {get_action_description(mode, 'left')}

😀😀😀 Modos disponibles 😀😀😀
  REPRO  : reproducción y navegación
  ROTAR  : rotación de imagen
  ZOOM   : acercar/alejar imagen
"""
    send_mpv({"command": ["show-text", text, 3000]})

def get_action_description(mode, button):
    if mode == "REPRO":
        return "←5s / video anterior" if button == "left" else "→5s / siguiente video"
    elif mode == "ROTAR":
        return "Rotar 180°"
    elif mode == "ZOOM":
        return "Zoom -5%" if button == "left" else "Zoom +5%"
    return "Sin acción"

# Acciones
playlist = []
current_index = [0]

def update_playlist():
    global playlist
    playlist = sorted(VIDEO_DIR.glob("*.mp4")) + sorted(VIDEO_DIR.glob("*.mov"))

def play_current():
    idx = current_index[0] % len(playlist)
    send_mpv({"command": ["playlist-play-index", idx]})
    send_mpv({"command": ["show-text", playlist[idx].name, 1000]})

def toggle_pause():
    send_mpv({"command": ["cycle", "pause"]})

def seek(offset):
    send_mpv({"command": ["add", "time-pos", offset]})

def rotate():
    send_mpv({"command": ["cycle-values", "video-rotate", "0", "180"]})

def zoom(delta):
    zoom_level[0] += delta
    zoom_level[0] = max(-1.0, min(1.0, zoom_level[0]))
    send_mpv({"command": ["set_property", "video-zoom", round(zoom_level[0], 2)]})

def next_video():
    current_index[0] = (current_index[0] + 1) % len(playlist)
    play_current()

def prev_video():
    current_index[0] = (current_index[0] - 1) % len(playlist)
    play_current()

def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))

def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

def handle_menu():
    duration = hold_duration(BTN_MENU)
    show_osd("Modo", "MENU")
    if duration < 0.5:
        if current_mode[0] == Mode.REPRO:
            toggle_pause()
    else:
        cycle_mode()

def handle_left():
    duration = hold_duration(BTN_LEFT)
    show_osd("Acción", "IZQUIERDA")
    if current_mode[0] == Mode.REPRO:
        if duration < 0.5:
            seek(-5)
        else:
            prev_video()
    elif current_mode[0] == Mode.ROTAR:
        rotate()
    elif current_mode[0] == Mode.ZOOM:
        zoom(-0.05)

def handle_right():
    duration = hold_duration(BTN_RIGHT)
    show_osd("Acción", "DERECHA")
    if current_mode[0] == Mode.REPRO:
        if duration < 0.5:
            seek(5)
        else:
            next_video()
    elif current_mode[0] == Mode.ROTAR:
        rotate()
    elif current_mode[0] == Mode.ZOOM:
        zoom(0.05)

# Sincronizar si hay USB
def find_usb_origins():
    for device in USB_MOUNT_ROOT.iterdir():
        path = device / USB_FOLDER_NAME
        if path.exists() and path.is_dir():
            return path
    return None

def sync_videos():
    usb_path = find_usb_origins()
    if not usb_path:
        return False

    for file in VIDEO_DIR.glob("*.mp4"):
        file.unlink()
    for file in VIDEO_DIR.glob("*.mov"):
        file.unlink()

    files = list(usb_path.glob("*.mp4")) + list(usb_path.glob("*.mov"))
    total = len(files)

    for i, file in enumerate(files):
        shutil.copy(file, VIDEO_DIR)
        progress = f"Copiando archivo {i+1}/{total}: {file.name}"
        send_mpv({"command": ["show-text", progress, 1500]})

    return True

def generate_playlist():
    with open(PLAYLIST_FILE, "w") as f:
        for video in sorted(VIDEO_DIR.glob("*.mp4")) + sorted(VIDEO_DIR.glob("*.mov")):
            f.write(str(video) + "\n")

def launch_mpv():
    os.system("pkill mpv")
    time.sleep(1)
    generate_playlist()
    subprocess.Popen([
        "mpv",
        "--fs", "--loop-playlist", "--no-config", "--no-osd-bar", "--osd-level=1",
        f"--playlist={PLAYLIST_FILE}",
        f"--input-ipc-server={SOCKET_PATH}",
        "--osd-font='Liberation Mono'",
        "--osd-font-size=26"
    ])

# Proceso de inicio
if sync_videos():
    print("USB detectada y sincronizada.")
else:
    print("No se detectó USB. Usando contenido existente.")

update_playlist()
launch_mpv()

BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

print("Reproductor autónomo iniciado.")
pause()
