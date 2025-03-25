import socket
import json
import socket as usocket

SOCKET_PATH = "/tmp/mpvsocket"
UDP_PORT = 5006

def send_mpv_command(command):
    client = usocket.socket(usocket.AF_UNIX, usocket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send(json.dumps(command).encode() + b'\n')
    client.close()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))
print("📡 Follower receptor en espera...")

while True:
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
        send_mpv_command({"command": ["cycle", "video-rotate"]})
