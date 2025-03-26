import socket
import time
import subprocess
import json
import os
import glob

VIDEO_DIR = "/home/pi/Videos"
SOCKET_PATH = "/tmp/mpvsocket"
BROADCAST_IP = "255.255.255.255"
SYNC_PORT = 5005

# Buscar todos los videos
def get_video_list():
    return sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))

video_list = get_video_list()
if not video_list:
    print("No se encontraron videos.")
    exit(1)

# Lanzar mpv con todos los videos en playlist
def launch_mpv_playlist():
    subprocess.Popen([
        "mpv", *video_list,
        "--fs", "--loop-playlist", "--no-terminal",
        "--hwdec=drm",
        f"--input-ipc-server={SOCKET_PATH}"
    ])
    wait_for_socket()

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        time.sleep(0.1)

def get_time_pos():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            return json.loads(response).get("data", 0)
    except:
        return 0

# Lanzar mpv
launch_mpv_playlist()
print("Reproducción iniciada.")
time.sleep(3)

# Preparar socket UDP para sincronización
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Enviar sincronización cada 10 segundos
while True:
    time_pos = get_time_pos()
    udp_sock.sendto(str(time_pos).encode(), (BROADCAST_IP, SYNC_PORT))
    time.sleep(10)
