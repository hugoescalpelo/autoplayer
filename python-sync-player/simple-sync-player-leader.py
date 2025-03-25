# master_sync.py
import socket
import time
import subprocess

VIDEO_PATH = "/home/pi/videos/videoA.mp4"
SLAVE_IP = "192.168.1.42"  # ← IP de la otra Raspberry Pi
PORT = 5005

def send_sync_signal():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b"PLAY", (SLAVE_IP, PORT))

def play_local_video():
    subprocess.Popen([
        "mpv", "--fs", "--no-osc", "--no-input-default-bindings",
        "--really-quiet", "--no-terminal", VIDEO_PATH
    ])

print("⌛ Esperando 3 segundos para sincronizar...")
time.sleep(3)
send_sync_signal()
print("📡 Señal enviada. Reproduciendo video...")
play_local_video()
