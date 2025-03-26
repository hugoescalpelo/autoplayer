import socket
import time
import subprocess
import json
import os

VIDEO_PATH = "/home/pitwo/Videos/VideoB.mp4"
PORT = 5005
SOCKET_PATH = "/tmp/mpvsocket"

def launch_mpv():
    subprocess.Popen([
        "mpv", VIDEO_PATH,
        "--fs", "--no-terminal", "--loop",
        f"--input-ipc-server={SOCKET_PATH}"
    ])
    print("🎬 Follower: Reproducción iniciada.")

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando que el socket de mpv esté disponible...")
        time.sleep(1)

def get_time_pos():
    for _ in range(3):
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            client.close()
            return json.loads(response).get("data", 0)
        except Exception as e:
            print(f"⚠️ Error al obtener tiempo: {e}")
            time.sleep(1)
    return 0

def seek_to(target):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps({"command": ["set_property", "time-pos", target]}).encode() + b'\n')
        client.close()
    except Exception as e:
        print(f"⚠️ Error al hacer seek: {e}")

launch_mpv()
wait_for_socket()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

while True:
    try:
        data, addr = sock.recvfrom(1024)
        leader_time = float(data.decode())
        current_time = get_time_pos()
        offset = abs(current_time - leader_time)

        if offset > 0.05:
            print(f"🔧 Corrigiendo desfase de {offset:.3f} segundos")
            seek_to(leader_time)
        else:
            print(f"✅ Sincronizado (offset {offset:.3f}s)")
    except Exception as e:
        print(f"❌ Error en la escucha UDP: {e}")
        time.sleep(1)
