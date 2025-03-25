# slave_sync.py
import socket
import subprocess

VIDEO_PATH = "/home/pi/videos/videoA.mp4"
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

print("👂 Esperando señal UDP para iniciar reproducción...")

while True:
    data, addr = sock.recvfrom(1024)
    if data == b"PLAY":
        print("🎬 Recibido PLAY. Reproduciendo video.")
        subprocess.Popen([
            "mpv", "--fs", "--no-osc", "--no-input-default-bindings",
            "--really-quiet", "--no-terminal", VIDEO_PATH
        ])
        break
