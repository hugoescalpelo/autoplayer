from gpiozero import Button
from signal import pause
import time
import socket
import json
import os
import glob
import re
from enum import IntEnum

# GPIO
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.05)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.05)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.05)

USER = os.getenv("USER") or "pi"
VIDEO_DIR = f"/home/{USER}/Videos"
SOCKET_PATH = "/tmp/mpvsocket"

# Modos
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2
    AB = 3

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# Playlist
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

def get_current_index():
    cat = category_list[category_index[0]]
    variants = [v for c, v, _ in playlist if c == cat]
    var = variants[variant_index[0] % len(variants)]
    for i, (c, v, _) in enumerate(playlist):
        if c == cat and v == var:
            return i
    return 0

def send_mpv(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except:
        pass

def show_osd(title, button):
    mode = current_mode[0].name
    text = f"""
+----------------------------+
| Modo actual: {mode:<11}       |
| Botón: {button:<10}           |
+----------------------------+

== Funciones del modo actual ==
  IZQUIERDA  : {get_action_description(mode, 'left')}
  DERECHA    : {get_action_description(mode, 'right')}
  MENÚ       : {get_action_description(mode, 'menu')}

== Cambiar modo ==
  Mantén presionado MENÚ para rotar entre modos.

== Modos disponibles ==
  REPRO      : reproducción y navegación
  ROTAR      : rotación del video
  ZOOM       : acercar y alejar imagen
  AB         : cambiar versión del video
"""
    send_mpv({"command": ["show-text", text, 3000]})

def get_action_description(mode, button):
    if mode == "REPRO":
        if button == "left":
            return "←5s / categoría anterior"
        elif button == "right":
            return "→5s / categoría siguiente"
        elif button == "menu":
            return "Pausa / reanudar"
    elif mode == "ROTAR":
        return "Rotar 180°"
    elif mode == "ZOOM":
        return "Zoom -5%" if button == "left" else "Zoom +5%"
    elif mode == "AB":
        return "Cambiar variante"

    return "Sin acción"

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
    send_mpv({"command": ["show-text", f"Reproduciendo: {playlist[idx][0]}{playlist[idx][1]}", 1000]})

def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))

def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

def handle_menu():
    duration = hold_duration(BTN_MENU)
    show_osd("Modo", "MENÚ")
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

def launch_mpv():
    files = [f for _, _, f in playlist]
    os.system("pkill mpv")
    time.sleep(1)
    os.system(
        f"mpv {' '.join(files)} "
        f"--fs --loop-playlist --no-config --no-osd-bar --osd-level=1 "
        f"--vo=gpu --hwdec=drm "
        f"--osd-font-size=18 --osd-font='Consolas' "
        f"--input-ipc-server={SOCKET_PATH} &"
    )

# Iniciar sistema
BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

launch_mpv()
print("Reproductor autónomo iniciado.")
pause()
