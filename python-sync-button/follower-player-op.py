import socket
import time
import subprocess
import json
import os
import glob

VIDEO_DIR = "/home/pitwo/Videos"
SOCKET_PATH = "/tmp/mpvsocket"
LISTEN_PORT = 5005

# Obtener lista de videos ordenados
def get_video_list():
    return sorted(glob.glob(os.path.join(VIDEO_DIR, "*.mp4")))

video_list = get_video_list()
if not video_list:
    print("No se encontraron videos.")
    exit(1)

# Lanzar mpv con la playlist completa
def launch_mpv():
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

def get_pause():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "pause"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            return json.loads(response).get("data", False)
    except:
        return False

# Lanzamiento inicial
launch_mpv()
print("Follower: reproducción iniciada.")
time.sleep(3)

# Socket UDP para recibir sincronización
sync_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sync_sock.bind(("", LISTEN_PORT))

last_sync = 0
print("Esperando señal de sincronización del líder...")

while True:
    sync_sock.settimeout(0.2)
    try:
        data, addr = sync_sock.recvfrom(1024)
        leader_time = float(data.decode().strip())
        now = time.time()

        if now - last_sync > 9:
            current_time = get_time_pos()
            offset = round(leader_time - current_time, 3)

            if not get_pause() and abs(offset) > 0.05:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.connect(SOCKET_PATH)
                    client.send(json.dumps({"command": ["set_property", "time-pos", leader_time]}).encode() + b'\n')
                print(f"Sincronizando video (desfase: {offset:+.3f}s)")

            last_sync = now

    except socket.timeout:
        continue
