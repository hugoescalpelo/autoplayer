import os
import random
import subprocess
import time

# Ruta base donde están las carpetas de categorías
BASE_PATH = "/home/pi/Documents/video_vertical"  # <- Modifica con la ruta real
DURACION_CATEGORIA = 40  # Segundos totales por categoría
DURACION_VIDEO_PROMEDIO = 10  # Duración estimada por video

def obtener_videos(categoria):
    """ Obtiene videos de la categoría recibida """
    categoria_path = os.path.join(BASE_PATH, categoria)
    texto_path = os.path.join(categoria_path, "texto")
    video_path = os.path.join(categoria_path, "video")

    videos_texto = [os.path.join(texto_path, v) for v in os.listdir(texto_path) if v.endswith('.mp4')] if os.path.exists(texto_path) else []
    videos_video = [os.path.join(video_path, v) for v in os.listdir(video_path) if v.endswith('.mp4')] if os.path.exists(video_path) else []

    if not videos_video:
        return []

    video_texto = random.choice(videos_texto) if videos_texto else None
    lista_videos = [video_texto] if video_texto else []

    duracion_actual = 0
    while duracion_actual < DURACION_CATEGORIA:
        video = random.choice(videos_video)
        lista_videos.append(video)
        duracion_actual += DURACION_VIDEO_PROMEDIO

    return lista_videos

def reproducir_video(video, duracion_restante):
    """ Reproduce un video rotado 90° """
    print(f"🎥 Reproduciendo (rotado 90°): {video} | Tiempo disponible: {duracion_restante:.1f} s")

    subprocess.run(["mpv", "--fs", "--really-quiet", "--no-terminal", "--video-rotate=90", "--length=" + str(duracion_restante), video])

def reproducir_videos(lista_videos):
    """ Reproduce los videos y ajusta el tiempo total a 40s """
    tiempo_inicio = time.time()

    for video in lista_videos:
        tiempo_restante = DURACION_CATEGORIA - (time.time() - tiempo_inicio)

        if tiempo_restante <= 0:
            break

        reproducir_video(video, min(tiempo_restante, DURACION_VIDEO_PROMEDIO))

def main():
    categorias = [cat for cat in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, cat))]

    while True:
        categoria = random.choice(categorias)
        print(f"\n🔄 Cambiando a categoría: {categoria}")

        videos_a_reproducir = obtener_videos(categoria)

        if videos_a_reproducir:
            reproducir_videos(videos_a_reproducir)
        else:
            print(f"⚠️ No hay suficientes videos en {categoria}")

        time.sleep(0.5)  # Pequeña pausa antes de la siguiente categoría

if __name__ == "__main__":
    main()
