import socket
import json
import socket as usocket
import os
import time

SOCKET_PATH = "/tmp/mpvsocket"
UDP_PORT = 5006

# Usamos una lista para almacenar el índice de modo
state = {"mode_index": 0}
modes = [
    {"command": ["cycle", "video-rotate"]},
    {"command": ["add", "video-zoom", 0.5]},
    {"command": ["add", "video-zoom", -0.5]},
    {"command": ["seek", 0, "absolute"]}
]

def wait_for_socket():
    while not os.path.exists(SOCKET_PATH):
        print("⏳ Esperando socket de mpv...")
        time.sleep(1)

def send_mpv_command(command):
    try:
        client = usocket.socket(usocket.AF_UNIX, usocket.SOCK_STREAM)
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
        print(f"🎬 Comando recibido: {command}")

        if command == "GLOBAL_TOGGLE_PLAY":
            send_mpv_command({"command": ["cycle", "pause"]})
        elif command == "GLOBAL_NEXT_GROUP":
            send_mpv_command({"command": ["set_property", "time-pos", 0]})
        elif command == "GLOBAL_PREV_GROUP":
            send_mpv_command({"command": ["set_property", "time-pos", 0]})
        elif command == "LOCAL_REWIND":
            send_mpv_command({"command": ["seek", -5, "relative"]})
        elif command == "LOCAL_FAST_FORWARD":
            send_mpv_command({"command": ["seek", 5, "relative"]})
        elif command == "LOCAL_CYCLE_MODE":
            current_mode = state["mode_index"]
            send_mpv_command(modes[current_mode])
            print(f"🔄 Ejecutando modo local: {modes[current_mode]}")
            state["mode_index"] = (current_mode + 1) % len(modes)

    except Exception as e:
        print(f"❌ Error en receptor UDP: {e}")
        time.sleep(1)
