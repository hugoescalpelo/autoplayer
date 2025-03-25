# master_trigger.py
import socket
import time
import subprocess

VIDEO_PATH = "/home/pione/Videos/videoA.mp4"
SLAVE_IP = "192.168.1.121"  # ← IP de la otra Raspberry Pi
PORT = 5005

# Iniciar el video en modo pausa
subprocess.Popen([
    "mpv", "--fs", "--no-terminal", "--pause", VIDEO_PATH
])

print("⌛ Preparando sincronización...")
time.sleep(3)  # Tiempo para que ambas carguen

# Enviar trigger
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b"START", (SLAVE_IP, PORT))
print("📡 Trigger enviado. También iniciando reproducción local.")

# Enviar "unpause" localmente
subprocess.run(["mpv", "ipc:///tmp/mpv-socket", "--input-ipc-server=/tmp/mpv-socket"], timeout=1)
