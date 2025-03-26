from gpiozero import Button
from signal import pause
import socket
import time
import json
import os
from enum import IntEnum

# GPIO
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.05)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.05)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.05)

# Red
UDP_IP_GLOBAL = "255.255.255.255"
UDP_PORT_GLOBAL = 5006
UDP_PORT_LOCAL = 5007
LOCAL_SOCKET_PATH = "/tmp/mpvsocket"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Modos
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2
    AB = 3

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# Enviar a mpv directamente
def send_local_mpv(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(LOCAL_SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except:
        print("⚠️")

# Enviar comandos globales (UDP broadcast)
def broadcast(command):
    try:
        sock.sendto(command.encode(), (UDP_IP_GLOBAL, UDP_PORT_GLOBAL))
    except:
        print("❌")

# Enviar comandos locales
def local(command):
    try:
        sock.sendto(command.encode(), ("127.0.0.1", UDP_PORT_LOCAL))
    except:
        print("💥")

# Acciones locales
def local_rotate_180():
    send_local_mpv({"command": ["cycle-values", "video-rotate", "0", "180"]})

def local_zoom_in():
    if zoom_level[0] < 1.0:
        zoom_level[0] += 0.05
        zoom_level[0] = round(zoom_level[0], 2)
        send_local_mpv({"command": ["set_property", "video-zoom", zoom_level[0]]})

def local_zoom_out():
    if zoom_level[0] > -1.0:
        zoom_level[0] -= 0.05
        zoom_level[0] = round(zoom_level[0], 2)
        send_local_mpv({"command": ["set_property", "video-zoom", zoom_level[0]]})

def local_switch_ab():
    local("LOCAL_SWITCH_AB")

# Cambiar modo
def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))
    print(f"🔁 {current_mode[0].name[0]}")

# Medir duración de presión
def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

# Acciones del botón MENU
def handle_menu():
    duration = hold_duration(BTN_MENU)
    if duration < 0.5:
        if current_mode[0] == Mode.REPRO:
            broadcast("GLOBAL_TOGGLE_PLAY")
            print("⏯️")
    else:
        cycle_mode()

# Acciones botón IZQUIERDO
def handle_left():
    duration = hold_duration(BTN_LEFT)
    mode = current_mode[0]
    if mode == Mode.REPRO:
        broadcast("GLOBAL_PREV_5" if duration < 0.5 else "GLOBAL_PREV_CATEGORY")
    elif mode == Mode.ROTAR:
        local_rotate_180()
    elif mode == Mode.ZOOM:
        local_zoom_out()
    elif mode == Mode.AB:
        local_switch_ab()

# Acciones botón DERECHO
def handle_right():
    duration = hold_duration(BTN_RIGHT)
    mode = current_mode[0]
    if mode == Mode.REPRO:
        broadcast("GLOBAL_NEXT_5" if duration < 0.5 else "GLOBAL_NEXT_CATEGORY")
    elif mode == Mode.ROTAR:
        local_rotate_180()
    elif mode == Mode.ZOOM:
        local_zoom_in()
    elif mode == Mode.AB:
        local_switch_ab()

# Asignar funciones a botones
BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

print("🎛️")
pause()
