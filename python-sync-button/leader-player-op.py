import socket
import time
import subprocess
import json
import os

VIDEO_PATH = "/home/pione/Videos/VideoA.mp4"  # Cambia esto si usas otra categoría
SOCKET_PATH = "/tmp/mpvsocket"
BROADCAST_IP = "255.255.255.255"
PORT = 5005

# Lanzar mpv con socket de control
subprocess.Popen([
    "mpv", VIDEO_PATH,
    "--fs", "--no-terminal", "--loop",
    "--hwdec=drm",  # o "rpi" o "v4l2" según tu configuración, evita "auto"
    f"--input-ipc-server={SOCKET_PATH}"
])
print("🎬 Leader: reproduciendo video en loop")

# Esperar a que el socket esté listo
while not os.path.exists(SOCKET_PATH):
    print("⏳ Esperando socket de mpv...")
    time.sleep(0.5)

# Función para obtener la posición actual del video
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

# Configurar socket UDP de broadcast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Bucle principal de sincronización
while True:
    current_time = get_time_pos()
    sock.sendto(str(current_time).encode(), (BROADCAST_IP, PORT))
    print(f"📡 Tiempo enviado: {current_time:.2f}s")
    time.sleep(10)
