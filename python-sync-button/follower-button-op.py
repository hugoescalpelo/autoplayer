from gpiozero import Button
from signal import pause
import socket
import time
from enum import IntEnum

# Pines GPIO
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.1)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.1)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.1)

# Red
UDP_PORT = 5007
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Modos de operación
class Mode(IntEnum):
    REPRO = 0
    ROTAR = 1
    ZOOM = 2
    AB = 3

current_mode = Mode.REPRO

def send_local(command):
    sock.sendto(command.encode(), ("127.0.0.1", UDP_PORT))
    print(f"📍 [LOCAL] {command}")

def cycle_mode():
    global current_mode
    current_mode = Mode((current_mode + 1) % len(Mode))
    print(f"🔁 Modo cambiado a: {current_mode.name}")

def handle_menu_press():
    start = time.time()
    while BTN_MENU.is_pressed:
        time.sleep(0.01)
    duration = time.time() - start

    if duration < 0.5:
        if current_mode == Mode.REPRO:
            send_local("GLOBAL_TOGGLE_PLAY")
    else:
        cycle_mode()

def handle_left_press():
    start = time.time()
    while BTN_LEFT.is_pressed:
        time.sleep(0.01)
    duration = time.time() - start

    if current_mode == Mode.REPRO:
        if duration < 0.5:
            send_local("GLOBAL_PREV_5")
        else:
            send_local("GLOBAL_PREV_CATEGORY")
    elif current_mode == Mode.ROTAR:
        send_local("LOCAL_ROTATE_180")
    elif current_mode == Mode.ZOOM:
        send_local("LOCAL_ZOOM_OUT")
    elif current_mode == Mode.AB:
        send_local("LOCAL_SWITCH_AB")

def handle_right_press():
    start = time.time()
    while BTN_RIGHT.is_pressed:
        time.sleep(0.01)
    duration = time.time() - start

    if current_mode == Mode.REPRO:
        if duration < 0.5:
            send_local("GLOBAL_NEXT_5")
        else:
            send_local("GLOBAL_NEXT_CATEGORY")
    elif current_mode == Mode.ROTAR:
        send_local("LOCAL_ROTATE_180")
    elif current_mode == Mode.ZOOM:
        send_local("LOCAL_ZOOM_IN")
    elif current_mode == Mode.AB:
        send_local("LOCAL_SWITCH_AB")

# Asignación de eventos
BTN_MENU.when_pressed = handle_menu_press
BTN_LEFT.when_pressed = handle_left_press
BTN_RIGHT.when_pressed = handle_right_press

print(f"🎛️ Botonera Follower activa — modo inicial: {current_mode.name}")
pause()
