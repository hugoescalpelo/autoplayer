import socket
import time
import subprocess
import datetime

VIDEO_PATH = "/home/pione/Videos/VideoA.mp4"
FOLLOWER_IP = "192.168.1.121"
PORT = 5005

# Calcular hora de reproducción (3 segundos en el futuro)
start_time = datetime.datetime.now() + datetime.timedelta(seconds=3)
start_str = start_time.strftime("%H:%M:%S")

print(f"⌛ Reproducción programada para: {start_str}")

# Enviar la hora al follower
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(start_str.encode(), (FOLLOWER_IP, PORT))

# Esperar hasta que llegue la hora
while datetime.datetime.now() < start_time:
    time.sleep(0.05)

# Reproducir video en loop
subprocess.run([
    "mpv", "--fs", "--no-terminal", "--loop", VIDEO_PATH
])
