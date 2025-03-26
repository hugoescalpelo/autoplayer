import socket
import time
import subprocess
import json
import os

VIDEO_PATH = "/home/pione/Videos/VideoA.mp4"
FOLLOWER_IP = "192.168.1.255"
PORT = 5005
SOCKET_PATH = "/tmp/mpvsocket"

subprocess.Popen([
    "mpv", VIDEO_PATH,
    "--fs", "--no-terminal", "--loop",
    f"--input-ipc-server={SOCKET_PATH}"
])
print("🎬 Leader: Reproducción iniciada.")

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

wait_for_socket()

def get_time_pos():
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
        response = client.recv(1024).decode()
        client.close()
        return json.loads(response).get("data", 0)
    except Exception as e:
        print(f"⚠️ Error obteniendo tiempo: {e}")
        return 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

while True:
    current_time = get_time_pos()
    sock.sendto(str(current_time).encode(), (FOLLOWER_IP, PORT))
    time.sleep(30)
