import os
import shutil
import subprocess
import json
import time
import socket
from pathlib import Path

# --- CONFIGURACIÓN ---
DEST_DIR = Path("/home/user/Videos")
USB_MOUNT_ROOT = Path("/media")
USB_FOLDER_NAME = "origins"
TEMP_DIR = Path("/tmp/converted_videos")
SOCKET_PATH = "/tmp/mpvsocket"
PLAYLIST_FILE = DEST_DIR / "playlist.m3u"

# --- PARÁMETROS DE VIDEO ---
EXPECTED_WIDTH = 1920
EXPECTED_HEIGHT = 1080
EXPECTED_FPS = 30
EXPECTED_BITRATE = 12000000
EXPECTED_CODEC = "h264"
EXPECTED_PROFILE = "High"
EXPECTED_LEVEL = "4.1"

# --- MOSTRAR MENSAJES OSD ---
def send_osd(msg):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        command = {"command": ["show-text", msg, 4000, 0]}
        client.send(json.dumps(command).encode() + b'\n')
        client.close()
    except:
        print(f"[OSD] {msg}")

# --- DETECTAR USB CON /origins ---
def find_usb_origins():
    for device in USB_MOUNT_ROOT.iterdir():
        path = device / USB_FOLDER_NAME
        if path.exists() and path.is_dir():
            return path
    return None

# --- VERIFICAR FORMATO DE VIDEO ---
def is_valid_video(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
            capture_output=True,
            text=True
        )
        info = json.loads(result.stdout)
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                codec = stream.get("codec_name")
                profile = stream.get("profile")
                width = stream.get("width")
                height = stream.get("height")
                level = str(float(stream.get("level", 0)) / 10)
                fps = eval(stream.get("r_frame_rate", "0/1"))
                bitrate = int(stream.get("bit_rate", 0))
                return (
                    codec == EXPECTED_CODEC and profile == EXPECTED_PROFILE and level == EXPECTED_LEVEL and
                    width == EXPECTED_WIDTH and height == EXPECTED_HEIGHT and
                    round(fps) == EXPECTED_FPS and abs(bitrate - EXPECTED_BITRATE) <= 1000000
                )
    except:
        return False
    return False

# --- CONVERTIR ARCHIVO A FORMATO VÁLIDO ---
def convert_to_valid_format(src, dst):
    if src.suffix.lower() == '.mp3':
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-f", "lavfi", "-i", "color=size=1920x1080:rate=30:color=black",
            "-i", str(src),
            "-shortest", "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1", "-b:v", "12M",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100",
            str(dst)
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1", "-b:v", "12M",
            "-vf", "scale=1920:1080,fps=30", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100",
            str(dst)
        ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- GENERAR PLAYLIST ---
def generate_playlist():
    with open(PLAYLIST_FILE, "w") as f:
        for video in sorted(DEST_DIR.glob("*.mp4")):
            f.write(str(video) + "\n")

# --- SINCRONIZAR VIDEOS ---
def sync_and_convert_videos():
    usb_path = find_usb_origins()
    if not usb_path:
        send_osd("No se detectó USB con /origins.")
        return False

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)

    send_osd("USB detectada. Iniciando sincronización...")

    for file in usb_path.glob("*"):
        if file.suffix.lower() not in [".mp4", ".mov", ".mp3"]:
            continue
        target = TEMP_DIR / (file.stem + ".mp4")

        if file.suffix.lower() == ".mp4" and is_valid_video(file):
            send_osd(f"Copiando {file.name}")
            shutil.copy(file, target)
        else:
            send_osd(f"Convirtiendo {file.name}")
            convert_to_valid_format(file, target)

    for f in DEST_DIR.glob("*.mp4"):
        f.unlink()
    for f in TEMP_DIR.glob("*.mp4"):
        shutil.copy(f, DEST_DIR)

    generate_playlist()
    send_osd("Sincronización completada.")
    return True

# --- ESPERAR A SOCKET DE MPV ---
def wait_for_socket():
    for _ in range(15):
        if Path(SOCKET_PATH).exists():
            return True
        time.sleep(1)
    return False

# --- INICIO DE REPRODUCCIÓN ---
subprocess.Popen([
    "mpv",
    "--fs", "--no-terminal", "--loop-playlist",
    "--playlist", str(PLAYLIST_FILE),
    f"--input-ipc-server={SOCKET_PATH}",
    "--osd-font='Liberation Mono'",
    "--osd-font-size=26"
])

# --- ESPERAR A SOCKET ---
if wait_for_socket():
    sync_and_convert_videos()
else:
    print("No se pudo iniciar el socket de MPV.")
