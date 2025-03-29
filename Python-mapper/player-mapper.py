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
UDP_PORT_STREAM = 1234

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
| Botón presionado: {button:<8}       |
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
        return "←5s / video anterior (mantén presionado)" if button == "left" else "→5s / siguiente video (mantén presionado)"
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
    playlist = sorted(VIDEO_DIR.glob("*.mp4")) + sorted(VIDEO_DIR.glob("*.MP4")) + \
               sorted(VIDEO_DIR.glob("*.mov")) + sorted(VIDEO_DIR.glob("*.MOV"))

def play_current():
    idx = current_index[0] % len(playlist)
    send_mpv({"command": ["loadfile", str(playlist[idx]), "replace"]})
    send_mpv({"command": ["show-text", playlist[idx].name, 1000]})
    send_mpv({"command": ["set_property", "loop-file", True]})

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

# Detectar transmisión UDP activa
def is_stream_active():
    try:
        result = subprocess.run(
            ["ss", "-u", "-n"], capture_output=True, text=True
        )
        return f":{UDP_PORT_STREAM}" in result.stdout
    except:
        return False

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
        print("No se encontró memoria USB con carpeta origins.")
        return False

    print("Sincronizando videos desde USB...")
    for file in VIDEO_DIR.glob("*.mp4") + VIDEO_DIR.glob("*.MP4") + \
                VIDEO_DIR.glob("*.mov") + VIDEO_DIR.glob("*.MOV"):
        file.unlink()

    all_videos = list(usb_path.glob("*.mp4")) + list(usb_path.glob("*.MP4")) + \
                 list(usb_path.glob("*.mov")) + list(usb_path.glob("*.MOV"))

    total = len(all_videos)
    for i, file in enumerate(all_videos, 1):
        print(f"[{i}/{total}] Copiando: {file.name}")
        shutil.copy(file, VIDEO_DIR)

    return True

def generate_playlist():
    with open(PLAYLIST_FILE, "w") as f:
        for video in sorted(VIDEO_DIR.glob("*.mp4")) + sorted(VIDEO_DIR.glob("*.MP4")) + \
                       sorted(VIDEO_DIR.glob("*.mov")) + sorted(VIDEO_DIR.glob("*.MOV")):
            f.write(str(video) + "\n")

def launch_mpv(source):
    os.system("pkill mpv")
    time.sleep(1)
    if source == "playlist":
        generate_playlist()
        cmd = [
            "mpv", str(playlist[0]), "--fs", "--loop-file", "--no-config", "--no-osd-bar", "--osd-level=1",
            f"--input-ipc-server={SOCKET_PATH}",
            "--osd-font='Liberation Mono'", "--osd-font-size=26"
        ]
    else:
        cmd = [
            "mpv", f"udp://@:{UDP_PORT_STREAM}", "--fs", "--no-terminal",
            f"--input-ipc-server={SOCKET_PATH}", "--osd-font='Liberation Mono'", "--osd-font-size=26"
        ]
    subprocess.Popen(cmd)

# Proceso de inicio
if sync_videos():
    print("USB detectada y videos sincronizados.")
else:
    print("No se detectó USB. Usando videos existentes.")

update_playlist()

# Detectar si hay transmisión activa
if is_stream_active():
    print("Stream detectado. Iniciando reproducción de stream.")
    launch_mpv("stream")
else:
    launch_mpv("playlist")

BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

print("Reproductor autónomo iniciado.")
pause()
