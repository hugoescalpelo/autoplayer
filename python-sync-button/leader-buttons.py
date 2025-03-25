from gpiozero import Button
from signal import pause
import socket
import time

# Pines GPIO personalizados
BTN_LEFT = Button(17, pull_up=True, bounce_time=0.1)   # Back
BTN_RIGHT = Button(22, pull_up=True, bounce_time=0.1)  # Next
BTN_MENU = Button(27, pull_up=True, bounce_time=0.1)   # Menu

# UDP broadcast para comandos globales
UDP_IP = "255.255.255.255"
UDP_PORT = 5006
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Enviar comando UDP
def send_global(command):
    print(f"🌐 Enviando comando global: {command}")
    sock.sendto(command.encode(), (UDP_IP, UDP_PORT))

# Ejecutar comando local
def execute_local(command):
    print(f"💻 Ejecutando comando local: {command}")
    # Aquí puedes comunicarte directamente con el mpv local (IPC)

# Función de gestión de pulsaciones
def handle_button(button_name, command_short, command_long):
    pressed_time = time.time()
    while button_name.is_pressed:
        time.sleep(0.01)
    duration = time.time() - pressed_time
    if duration < 0.5:
        if command_short.startswith("GLOBAL_"):
            send_global(command_short)
        else:
            execute_local(command_short)
    else:
        if command_long.startswith("GLOBAL_"):
            send_global(command_long)
        else:
            execute_local(command_long)

# Asignación de botones a acciones
BTN_LEFT.when_pressed = lambda: handle_button(BTN_LEFT, "GLOBAL_PREV_GROUP", "LOCAL_REWIND")
BTN_RIGHT.when_pressed = lambda: handle_button(BTN_RIGHT, "GLOBAL_NEXT_GROUP", "LOCAL_FAST_FORWARD")
BTN_MENU.when_pressed = lambda: handle_button(BTN_MENU, "GLOBAL_TOGGLE_PLAY", "LOCAL_CYCLE_MODE")

print("🎛️ Controlador GPIO (3 botones) listo.")
pause()
