import socket
import json
import socket as usocket
import os
import time

SOCKET_PATH = "/tmp/mpvsocket"
UDP_PORT = 5006
CONTROL_PORT = 5007

rotation_state = 0
zoom_level = 0.0  # MPV default zoom is 0.0

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

def send_mpv_command(command):
    try:
        client = usocket.socket(usocket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.send(json.dumps(command).encode() + b'\n')
        client.close()
    except Exception as e:
        print(f"⚠️ Error enviando comando a mpv: {e}")

def send_local_command(command_str):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(command_str.encode(), ("127.0.0.1", CONTROL_PORT))
    except Exception as e:
        print(f"⚠️ Error enviando comando local: {e}")

wait_for_socket()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))
print("📡 Leader receptor en espera...")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        command = data.decode().strip()
        print(f"🌐 Comando recibido: {command}")

        if command == "GLOBAL_TOGGLE_PLAY":
            send_mpv_command({"command": ["cycle", "pause"]})

        elif command == "GLOBAL_NEXT_GROUP":
            send_mpv_command({"command": ["seek", 5, "relative"]})

        elif command == "GLOBAL_PREV_GROUP":
            send_mpv_command({"command": ["seek", -5, "relative"]})

        elif command == "LOCAL_ROTATE":
            if rotation_state == 0:
                rotation_state = 180
            elif rotation_state == 180:
                rotation_state = 0
            print(f"🔄 Rotando a {rotation_state} grados")
            send_mpv_command({"command": ["set_property", "video-rotate", rotation_state]})

        elif command == "LOCAL_ZOOM_IN":
            if zoom_level < 1.0:
                zoom_level += 0.05
                zoom_level = round(zoom_level, 2)
                print(f"🔍 Zoom in: {zoom_level}")
                send_mpv_command({"command": ["set_property", "video-zoom", zoom_level]})

        elif command == "LOCAL_ZOOM_OUT":
            if zoom_level > -0.9:
                zoom_level -= 0.05
                zoom_level = round(zoom_level, 2)
                print(f"🔎 Zoom out: {zoom_level}")
                send_mpv_command({"command": ["set_property", "video-zoom", zoom_level]})

        elif command == "LOCAL_SWITCH_VARIANT":
            print("🅰️ Cambiando variante de video")
            send_local_command("LOCAL_SWITCH_VARIANT")

    except Exception as e:
        print(f"❌ Error en receptor UDP: {e}")
        time.sleep(1)
