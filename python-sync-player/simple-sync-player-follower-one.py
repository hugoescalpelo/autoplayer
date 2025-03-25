# slave_listener.py
import socket
import subprocess
import time

VIDEO_PATH = "/home/pitwo/Videos/videoB.mp4"
PORT = 5005

# Precargar el video en pausa
subprocess.Popen([
    "mpv", "--fs", "--no-terminal", "--pause", VIDEO_PATH
])

print("👂 Esperando trigger desde master...")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

while True:
    data, addr = sock.recvfrom(1024)
    if data == b"START":
        print("🎬 Recibido trigger. Iniciando video.")
        subprocess.run(["mpv", "ipc:///tmp/mpv-socket", "--input-ipc-server=/tmp/mpv-socket"], timeout=1)
        break
