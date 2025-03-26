import socket
import json
import os
import time

SOCKET_PATH = "/tmp/mpvsocket"
UDP_PORT = 5006

# Estado de zoom
zoom_level = [1.0]  # porcentaje (1.0 = 100%)

# Categorías y video A/B
video_set = {
    "current_category": "DEFAULT",
    "ab": "A"  # puede ser "A" o "B"
}

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

def send_mpv_command(command):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps(command).encode() + b'\n')
        client.close()
    except Exception as e:
        print(f"⚠️ Error enviando comando a mpv: {e}")

wait_for_socket()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))
print("📡 Follower receptor en espera...")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        command = data.decode().strip()
        print(f"📨 Comando recibido: {command}")

        if command == "GLOBAL_TOGGLE_PLAY":
            send_mpv_command({"command": ["cycle", "pause"]})

        elif command == "GLOBAL_NEXT_5":
            send_mpv_command({"command": ["seek", 5, "relative"]})

        elif command == "GLOBAL_PREV_5":
            send_mpv_command({"command": ["seek", -5, "relative"]})

        elif command == "GLOBAL_NEXT_CATEGORY":
            send_mpv_command({"command": ["set_property", "time-pos", 0]})
            # Aquí podrías agregar lógica para cambiar carpeta/categoría

        elif command == "GLOBAL_PREV_CATEGORY":
            send_mpv_command({"command": ["set_property", "time-pos", 0]})
            # Igual que arriba

        elif command == "LOCAL_ROTATE_180":
            send_mpv_command({"command": ["add", "video-rotate", 180]})

        elif command == "LOCAL_ZOOM_IN":
            if zoom_level[0] < 2.0:
                zoom_level[0] += 0.05
                send_mpv_command({"command": ["set_property", "video-zoom", zoom_level[0]]})
                print(f"🔍 Zoom in: {int(zoom_level[0]*100)}%")

        elif command == "LOCAL_ZOOM_OUT":
            if zoom_level[0] > 0.1:
                zoom_level[0] -= 0.05
                send_mpv_command({"command": ["set_property", "video-zoom", zoom_level[0]]})
                print(f"🔎 Zoom out: {int(zoom_level[0]*100)}%")

        elif command == "LOCAL_SWITCH_AB":
            video_set["ab"] = "B" if video_set["ab"] == "A" else "A"
            print(f"🔁 Cambiando a video {video_set['ab']}")
            # Aquí podrías reiniciar el video actual o cargar otro si lo integras con leader-sync más adelante

    except Exception as e:
        print(f"❌ Error en receptor UDP: {e}")
        time.sleep(1)
