# slave_listener.py
import socket
import subprocess
import time
import os

VIDEO_PATH = "/home/pitwo/Videos/VideoB.mp4"
PORT = 5005

# Iniciar mpv en pausa y fullscreen
print("🕒 Cargando video en pausa...")
mpv_proc = subprocess.Popen([
    "mpv", "--fs", "--pause", "--no-terminal", VIDEO_PATH
])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

print("👂 Esperando trigger del master...")

while True:
    data, addr = sock.recvfrom(1024)
    if data == b"START":
        print("🎬 Recibido trigger. Despausando...")
        # Enviar tecla 'p' al proceso de mpv
        os.system("xdotool search --class mpv key p")
        break
