import os
import random
import subprocess
import time

# Esperar 10 segundos para asegurarse de que X11 esté listo
time.sleep(10)

# Ruta base donde están las carpetas de categorías
BASE_PATH = "/ruta/a/tus/videos"  # <- Modifica con la ruta real
DURACION_TOTAL_PLAYLIST = 36000  # 10 horas en segundos
DURACION_VIDEO_PROMEDIO = 10  # Estimado de duración por video

def obtener_videos(categoria):
    """ Obtiene 1 video de texto y 3 de video para la categoría seleccionada """
    categoria_path = os.path.join(BASE_PATH, categoria)
    texto_path = os.path.join(categoria_path, "texto")
    video_path = os.path.join(categoria_path, "video")

    # Obtener listas de videos
    videos_texto = [os.path.join(texto_path, v) for v in os.listdir(texto_path) if v.endswith('.mp4')] if os.path.exists(texto_path) else []
    videos_video = [os.path.join(video_path, v) for v in os.listdir(video_path) if v.endswith('.mp4')] if os.path.exists(video_path) else []

    # Seleccionar 1 video de texto (si existe)
    video_texto = random.choice(videos_texto) if videos_texto else None
    lista_videos = [video_texto] if video_texto else []

    # Seleccionar 3 videos de video (si hay suficientes)
    videos_seleccionados = random.sample(videos_video, min(len(videos_video), 3))
    lista_videos.extend(videos_seleccionados)

    return lista_videos

def generar_playlist():
    """ Genera una playlist de 10 horas con la estructura correcta """
    categorias = [cat for cat in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, cat))]
    playlist = []
    duracion_actual = 0

    while duracion_actual < DURACION_TOTAL_PLAYLIST:
        categoria = random.choice(categorias)
        videos_categoria = obtener_videos(categoria)
        
        if videos_categoria:
            playlist.extend(videos_categoria)
            duracion_actual += len(videos_categoria) * DURACION_VIDEO_PROMEDIO

    return playlist

def reproducir_playlist(playlist):
    """ Guarda la playlist en un archivo y la reproduce con mpv sin interrupciones y con Stretch """
    playlist_path = "/tmp/playlist.txt"
    with open(playlist_path, "w") as f:
        for video in playlist:
            f.write(f"{video}\n")

    print("🎥 Reproduciendo playlist de 10 horas sin interrupciones y con Stretch...")
    subprocess.run([
        "mpv", "--fs", "--really-quiet", "--no-terminal", "--video-rotate=90",
        "--no-keepaspect", "--video-aspect-override=1", "--playlist=" + playlist_path
    ])

def main():
    while True:  # Se ejecuta en bucle infinito
        playlist = generar_playlist()
        reproducir_playlist(playlist)

if __name__ == "__main__":
    main()
