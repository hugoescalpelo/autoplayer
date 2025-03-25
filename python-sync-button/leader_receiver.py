import socket
import json
import socket as usocket
import os
import time

SOCKET_PATH = "/tmp/mpvsocket"
UDP_PORT = 5006

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
print("📡 Leader receptor en espera...")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        command = data.decode().strip()
        print(f"🌐 Comando recibido: {command}")

        if command == "GLOBAL_TOGGLE_PLAY":
            send_mpv_command({"command": ["cycle", "pause"]})
        elif command == "GLOBAL_NEXT_GROUP":
            send_mpv_command({"command": ["set_property", "time-pos", 0]})
        elif command == "GLOBAL_PREV_GROUP":
            send_mpv_command({"command": ["set_property", "time-pos", 0]})
    except Exception as e:
        print(f"❌ Error en receptor UDP: {e}")
        time.sleep(1)
