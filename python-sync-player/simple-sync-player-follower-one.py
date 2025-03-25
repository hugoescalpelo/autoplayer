import socket
import time
import subprocess
import datetime

VIDEO_PATH = "/home/pitwo/Videos/VideoB.mp4"
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

print("👂 Esperando hora de reproducción...")

data, addr = sock.recvfrom(1024)
start_str = data.decode().strip()
print(f"🎯 Reproducción programada para: {start_str}")

# Convertir a objeto datetime completo
today = datetime.date.today()
target_time = datetime.datetime.strptime(start_str, "%H:%M:%S").replace(
    year=today.year, month=today.month, day=today.day
)

# Esperar hasta que llegue la hora
while datetime.datetime.now() < target_time:
    time.sleep(0.05)

# Reproducir video en loop
subprocess.run([
    "mpv", "--fs", "--no-terminal", "--loop", VIDEO_PATH
])
