import socket
import time
import subprocess
import json

VIDEO_PATH = "/home/pitwo/Videos/VideoB.mp4"
PORT = 5005
SOCKET_PATH = "/tmp/mpvsocket"

# Lanzar mpv con IPC habilitado
subprocess.Popen([
    "mpv", VIDEO_PATH,
    "--fs", "--no-terminal", "--loop",
    f"--input-ipc-server={SOCKET_PATH}"
])
print("🎬 Follower: Reproducción iniciada con socket.")

# Esperar tiempo del leader
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
data, addr = sock.recvfrom(1024)
leader_time = float(data.decode())
print(f"⏱ Follower: Recibido tiempo del leader: {leader_time:.3f}")

# Obtener tiempo actual desde mpv
def get_time_pos():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
    response = client.recv(1024).decode()
    client.close()
    return json.loads(response).get("data", 0)

# Hacer seek si hay diferencia
current_time = get_time_pos()
offset = abs(current_time - leader_time)
if offset > 0.05:
    print(f"🔧 Follower: Corrigiendo desfase de {offset:.3f} segundos")
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send(json.dumps({"command": ["set_property", "time-pos", leader_time]}).encode() + b'\n')
    client.close()
else:
    print("✅ Follower: Ya está sincronizado.")
