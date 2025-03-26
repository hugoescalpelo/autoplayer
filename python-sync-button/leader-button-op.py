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

# Socket local de mpv
LOCAL_SOCKET_PATH = "/tmp/mpvsocket"

# Estados
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2
    AB = 3

current_mode = [Mode.REPRO]
zoom_level = [0.0]

# Enviar comandos directamente al socket de mpv
def send_mpv_command(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(LOCAL_SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except Exception as e:
        print(f"Error enviando a mpv: {e}")

# Acciones locales
def rotate_180():
    send_mpv_command({"command": ["cycle-values", "video-rotate", "0", "180"]})

def zoom_in():
    if zoom_level[0] < 1.0:
        zoom_level[0] += 0.05
        zoom_level[0] = round(zoom_level[0], 2)
        send_mpv_command({"command": ["set_property", "video-zoom", zoom_level[0]]})

def zoom_out():
    if zoom_level[0] > -1.0:
        zoom_level[0] -= 0.05
        zoom_level[0] = round(zoom_level[0], 2)
        send_mpv_command({"command": ["set_property", "video-zoom", zoom_level[0]]})

def toggle_pause():
    send_mpv_command({"command": ["cycle", "pause"]})

def skip_forward():
    send_mpv_command({"command": ["add", "time-pos", 5]})

def skip_backward():
    send_mpv_command({"command": ["add", "time-pos", -5]})

def switch_ab():
    send_mpv_command({"command": ["write-watch-later-config"]})  # Este comando es simbólico, puedes personalizarlo si tienes lógica A/B externa

def next_category():
    send_mpv_command({"command": ["write-watch-later-config"]})  # También simbólico

def prev_category():
    send_mpv_command({"command": ["write-watch-later-config"]})  # También simbólico

# Cambio de modo
def cycle_mode():
    current_mode[0] = Mode((current_mode[0] + 1) % len(Mode))
    mode_name = {
        Mode.REPRO: "REPRODUCCIÓN",
        Mode.ROTAR: "ROTAR",
        Mode.ZOOM: "ZOOM",
        Mode.AB: "CAMBIO A/B"
    }[current_mode[0]]
    print(f"Modo cambiado a: {mode_name}")

# Medición de duración del botón
def hold_duration(button):
    start = time.monotonic()
    while button.is_pressed:
        time.sleep(0.01)
    return time.monotonic() - start

# Botón menú
def handle_menu():
    duration = hold_duration(BTN_MENU)
    if duration < 0.5:
        if current_mode[0] == Mode.REPRO:
            toggle_pause()
            print("Reproducir/Pausar")
    else:
        cycle_mode()

# Botón izquierdo
def handle_left():
    duration = hold_duration(BTN_LEFT)
    mode = current_mode[0]
    if mode == Mode.REPRO:
        if duration < 0.5:
            skip_backward()
            print("Retroceder 5 segundos")
        else:
            prev_category()
            print("Categoría anterior")
    elif mode == Mode.ROTAR:
        rotate_180()
        print("Rotar 180 grados")
    elif mode == Mode.ZOOM:
        zoom_out()
        print("Reducir zoom")
    elif mode == Mode.AB:
        switch_ab()
        print("Cambiar variante A/B")

# Botón derecho
def handle_right():
    duration = hold_duration(BTN_RIGHT)
    mode = current_mode[0]
    if mode == Mode.REPRO:
        if duration < 0.5:
            skip_forward()
            print("Avanzar 5 segundos")
        else:
            next_category()
            print("Siguiente categoría")
    elif mode == Mode.ROTAR:
        rotate_180()
        print("Rotar 180 grados")
    elif mode == Mode.ZOOM:
        zoom_in()
        print("Aumentar zoom")
    elif mode == Mode.AB:
        switch_ab()
        print("Cambiar variante A/B")

# Asignar eventos a botones
BTN_MENU.when_pressed = handle_menu
BTN_LEFT.when_pressed = handle_left
BTN_RIGHT.when_pressed = handle_right

print("Controles de botones locales activados.")
pause()
