# simple-sync-player-follower-one.py
import socket
import time
import subprocess

VIDEO_PATH = "/home/pitwo/Videos/VideoB.mp4"
PORT = 5005

# Escuchar hora del leader
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

print("👂 Esperando hora desde leader...")
data, addr = sock.recvfrom(1024)
t0 = float(data.decode().strip())
t1 = time.time()

# Calcular diferencia entre relojes
drift = t1 - t0
print(f"⏱️  Drift estimado: {drift:.6f} segundos")

# Calcular hora de reproducción ajustada
start_time = t1 + 2 - drift
print(f"🎯 Reproducción ajustada para: {start_time:.6f}")

# Esperar hasta ese momento
while time.time() < start_time:
    time.sleep(0.01)

# Reproducir video en loop
subprocess.run([
    "mpv", "--fs", "--no-terminal", "--loop", VIDEO_PATH
])
