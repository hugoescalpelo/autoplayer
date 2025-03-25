# simple-sync-player-leader.py
import socket
import time
import subprocess

VIDEO_PATH = "/home/pione/Videos/VideoA.mp4"
FOLLOWER_IP = "192.168.1.121"
PORT = 5005

# Esperar 1 segundo antes de enviar
time.sleep(1)

# Obtener hora actual (precisa)
t0 = time.time()

# Enviar t0 al follower
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(str(t0).encode(), (FOLLOWER_IP, PORT))
print(f"📡 Hora enviada al follower: {t0:.6f}")

# Programar inicio 2 segundos después de enviar
start_time = t0 + 2

# Esperar hasta ese momento
while time.time() < start_time:
    time.sleep(0.01)

# Reproducir video en loop
subprocess.run([
    "mpv", "--fs", "--no-terminal", "--loop", VIDEO_PATH
])
