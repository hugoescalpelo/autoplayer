# master_trigger.py
import socket
import time
import subprocess
import os

VIDEO_PATH = "/home/pione/Videos/videoA.mp4"
SLAVE_IP = "192.168.1.121"  # Cambia esto por la IP de la slave
PORT = 5005

# Iniciar mpv en pausa
print("🕒 Cargando video en pausa...")
subprocess.Popen([
    "mpv", "--fs", "--pause", "--no-terminal", VIDEO_PATH
])

# Dar tiempo para cargar
time.sleep(3)

# Enviar trigger UDP
print("📡 Enviando señal START a slave...")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b"START", (SLAVE_IP, PORT))

# Enviar tecla 'p' al proceso de mpv local
print("🎬 Despausando video local...")
os.system("xdotool search --class mpv key p")
