from gpiozero import Button
from signal import pause
import socket
import time

# Pines físicos
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.1)
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.1)
BTN_MENU = Button(27, pull_up=True, bounce_time=0.1)

# Envío por UDP
UDP_IP = "255.255.255.255"
UDP_PORT = 5006
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

def send_global(command):
    print(f"🌐 Enviando comando global: {command}")
    sock.sendto(command.encode(), (UDP_IP, UDP_PORT))

def execute_local(command):
    print(f"💻 Ejecutando comando local: {command}")
    sock.sendto(command.encode(), ("127.0.0.1", UDP_PORT))

def handle_button(button, short_cmd, long_cmd):
    pressed_time = time.time()
    while button.is_pressed:
        time.sleep(0.01)
    duration = time.time() - pressed_time
    if duration < 0.5:
        (send_global if "GLOBAL" in short_cmd else execute_local)(short_cmd)
    else:
        (send_global if "GLOBAL" in long_cmd else execute_local)(long_cmd)

BTN_LEFT.when_pressed = lambda: handle_button(BTN_LEFT, "GLOBAL_PREV_GROUP", "LOCAL_REWIND")
BTN_RIGHT.when_pressed = lambda: handle_button(BTN_RIGHT, "GLOBAL_NEXT_GROUP", "LOCAL_FAST_FORWARD")
BTN_MENU.when_pressed = lambda: handle_button(BTN_MENU, "GLOBAL_TOGGLE_PLAY", "LOCAL_CYCLE_MODE")

print("🎛️ Controlador de botones listo.")
pause()
