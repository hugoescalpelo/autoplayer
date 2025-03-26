import socket
import time
import subprocess
import json
import os

VIDEO_PATH = "/home/pitwo/Videos/VideoB.mp4"
SOCKET_PATH = "/tmp/mpvsocket"
PORT = 5005

# Lanzar mpv en modo optimizado
subprocess.Popen([
    "mpv", VIDEO_PATH,
    "--fs", "--no-terminal", "--loop",
    "--hwdec=drm", "--untimed", "--no-cache", "--no-config",
    f"--input-ipc-server={SOCKET_PATH}"
])
print("🎬 Follower: Reproducción iniciada.")
time.sleep(3)

# Funciones auxiliares
def send_mpv_command(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps(command).encode() + b'\n')
    except Exception as e:
        print(f"⚠️ Error enviando a mpv: {e}")

def get_time_pos():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            return json.loads(response).get("data", 0)
    except Exception as e:
        print(f"⚠️ Error leyendo tiempo: {e}")
        return 0

def get_pause_state():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.send(json.dumps({"command": ["get_property", "pause"]}).encode() + b'\n')
            response = client.recv(1024).decode()
            return json.loads(response).get("data", False)
    except:
        return False

# Configurar socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

print("📡 Esperando sincronización del líder...")

while True:
    try:
        data, _ = sock.recvfrom(1024)
        leader_time = float(data.decode())
        current_time = get_time_pos()
        pause_state = get_pause_state()
        offset = abs(current_time - leader_time)

        if offset > 0.08:
            print(f"🔧 Corrigiendo desfase: Δ={offset:.3f}s")
            if offset < 0.5:
                send_mpv_command({"command": ["seek", leader_time, "absolute+exact"]})
            else:
                send_mpv_command({"command": ["set_property", "time-pos", leader_time]})
        else:
            print(f"✅ Sincronizado (Δ={offset:.3f}s)")
    except Exception as e:
        print(f"❌ Error de sincronización: {e}")
        time.sleep(0.5)
