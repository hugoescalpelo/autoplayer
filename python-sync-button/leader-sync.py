import socket
import time
import subprocess
import json

VIDEO_PATH = "/home/user/Videos/VideoA.mp4"
FOLLOWER_IP = "192.168.1.255"  # Broadcast para todas las Pi
PORT = 5005
SOCKET_PATH = "/tmp/mpvsocket"

# Lanzar mpv en loop con socket
subprocess.Popen([
    "mpv", VIDEO_PATH,
    "--fs", "--no-terminal", "--loop",
    f"--input-ipc-server={SOCKET_PATH}"
])
print("🎬 Leader: Reproducción iniciada.")
time.sleep(3)

def get_time_pos():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
    response = client.recv(1024).decode()
    client.close()
    return json.loads(response).get("data", 0)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Enviar sincronización cada 30 segundos
while True:
    current_time = get_time_pos()
    sock.sendto(str(current_time).encode(), (FOLLOWER_IP, PORT))
    time.sleep(30)
