import socket
import time
import subprocess
import json

VIDEO_PATH = "/home/pione/Videos/VideoA.mp4"
FOLLOWER_IP = "192.168.1.121"
PORT = 5005
SOCKET_PATH = "/tmp/mpvsocket"

# Lanzar mpv con IPC habilitado
subprocess.Popen([
    "mpv", VIDEO_PATH,
    "--fs", "--no-terminal", "--loop",
    f"--input-ipc-server={SOCKET_PATH}"
])
print("🎬 Leader: Reproducción iniciada con socket.")

# Esperar 3 segundos antes de sincronizar
time.sleep(3)

# Obtener tiempo actual desde mpv
def get_time_pos():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
    response = client.recv(1024).decode()
    client.close()
    return json.loads(response).get("data", 0)

current_time = get_time_pos()
print(f"⏱ Leader: Enviando tiempo actual {current_time:.3f} al follower.")

# Enviar a follower
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(str(current_time).encode(), (FOLLOWER_IP, PORT))
