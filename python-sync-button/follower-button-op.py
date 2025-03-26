from gpiozero import Button
from signal import pause
import socket
import time
import json
import os
import glob
import re
from enum import IntEnum

# GPIO
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.05)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.05)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.05)

SOCKET_PATH = "/tmp/mpvsocket"
VIDEO_DIR = "/home/pitwo/Videos"

# Modos
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2
    AB = 3

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# Construir playlist
def build_playlist():
    pattern = re.compile(r"^(.*?)([A-Z])\.mp4$")
    files = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))
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

# Obtener índice actual
def get_current_index():
    cat = category_list[category_index[0]]
    variants = [v for c, v, _ in playlist if c == cat]
    var = variants[variant_index[0] % len(variants)]
    for i, (c, v, _) in enumerate(playlist):
        if c == cat and v == var:
            return i
    return 0

# Enviar comando a mpv
def send_mpv(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except:
        pass

# Acciones
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
    index = get_current_index()
    send_mpv({"command": ["playlist-play-index", index]})
    print(f"Video {index}: {playlist[index][0]}{playlist[index][1]}")

# Cambio de modo
def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))
    print(f"Modo: {current_mode[0].name}")

# Duración del botón
def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

# Botón menú
def handle_menu():
    duration = hold_duration(BTN_MENU)
    if duration < 0.5 and current_mode[0] == Mode.REPRO:
        toggle_pause()
    elif duration >= 0.5:
        cycle_mode()

# Botón izquierdo
def handle_left():
    duration = hold_duration(BTN_LEFT)
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

# Botón derecho
def handle_right():
    duration = hold_duration(BTN_RIGHT)
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

# Asignar acciones
BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

print("Botonera activa — modo inicial: REPRO")
pause()
