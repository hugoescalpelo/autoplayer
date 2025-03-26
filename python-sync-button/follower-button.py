from gpiozero import Button
from signal import pause
import socket
import time

# Pines GPIO
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.1)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.1)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.1)

# Red
UDP_IP_GLOBAL = "255.255.255.255"
UDP_PORT = 5006
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

MODES = ["REPRO", "ROTAR", "ZOOM", "AB"]
current_mode = [0]  # usamos lista para mantener referencia mutable

def broadcast(command):
    print(f"🌍 [GLOBAL] {command}")
    sock.sendto(command.encode(), (UDP_IP_GLOBAL, UDP_PORT))

def local(command):
    print(f"📍 [LOCAL] {command}")
    sock.sendto(command.encode(), ("127.0.0.1", UDP_PORT))

def cycle_mode():
    current_mode[0] = (current_mode[0] + 1) % len(MODES)
    print(f"🔁 Modo cambiado a: {MODES[current_mode[0]]}")

def handle_menu_press():
    start = time.time()
    while BTN_MENU.is_pressed:
        time.sleep(0.01)
    duration = time.time() - start

    if duration < 0.5:
        if MODES[current_mode[0]] == "REPRO":
            broadcast("GLOBAL_TOGGLE_PLAY")
    else:
        cycle_mode()

def handle_left_press():
    mode = MODES[current_mode[0]]
    start = time.time()
    while BTN_LEFT.is_pressed:
        time.sleep(0.01)
    duration = time.time() - start

    if mode == "REPRO":
        if duration < 0.5:
            broadcast("GLOBAL_PREV_5")
        else:
            broadcast("GLOBAL_PREV_CATEGORY")
    elif mode == "ROTAR":
        local("LOCAL_ROTATE_180")
    elif mode == "ZOOM":
        local("LOCAL_ZOOM_OUT")
    elif mode == "AB":
        local("LOCAL_SWITCH_AB")

def handle_right_press():
    mode = MODES[current_mode[0]]
    start = time.time()
    while BTN_RIGHT.is_pressed:
        time.sleep(0.01)
    duration = time.time() - start

    if mode == "REPRO":
        if duration < 0.5:
            broadcast("GLOBAL_NEXT_5")
        else:
            broadcast("GLOBAL_NEXT_CATEGORY")
    elif mode == "ROTAR":
        local("LOCAL_ROTATE_180")
    elif mode == "ZOOM":
        local("LOCAL_ZOOM_IN")
    elif mode == "AB":
        local("LOCAL_SWITCH_AB")

BTN_MENU.when_pressed = handle_menu_press
BTN_LEFT.when_pressed = handle_left_press
BTN_RIGHT.when_pressed = handle_right_press

print("🎛️ Botonera activa — modo inicial: REPRO")
pause()
