import os
import random
import subprocess
import time

# Ruta base donde están las 10 carpetas de categorías
BASE_PATH = "/ruta/a/tus/videos"  # <- Modifica esto con la ruta real

def obtener_videos(categoria_path):
    """ Obtiene videos de la carpeta de texto y video """
    texto_path = os.path.join(categoria_path, "texto")
    video_path = os.path.join(categoria_path, "video")

    # Obtener lista de videos
    videos_texto = [os.path.join(texto_path, v) for v in os.listdir(texto_path) if v.endswith(('.mp4', '.avi', '.mkv'))] if os.path.exists(texto_path) else []
    videos_video = [os.path.join(video_path, v) for v in os.listdir(video_path) if v.endswith(('.mp4', '.avi', '.mkv'))] if os.path.exists(video_path) else []

    if not videos_video:
        return []  # Si no hay videos en 'video', no se puede reproducir nada

    # Verificar si la carpeta es MACROS-FUERZAS
    es_macros_fuerzas = os.path.basename(categoria_path) == "MACROS-FUERZAS"

    # Si no es MACROS-FUERZAS y hay videos en texto, seleccionar uno
    video_texto = random.choice(videos_texto) if videos_texto and not es_macros_fuerzas else None

    # Seleccionar 3 videos de 'video'
    cantidad_videos = 4 if video_texto else 3
    videos_video = random.sample(videos_video, min(len(videos_video), cantidad_videos))

    # Retornar lista de reproducción en el orden correcto
    return ([video_texto] if video_texto else []) + videos_video

def reproducir_videos(lista_videos):
    """ Reproduce una lista de videos con mpv """
    for video in lista_videos:
        print(f"Reproduciendo: {video}")
        subprocess.run(["mpv", "--fs", video])  # --fs para pantalla completa

def main():
    while True:
        categorias = [os.path.join(BASE_PATH, cat) for cat in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, cat))]

        for categoria in categorias:
            print(f"\nProcesando categoría: {categoria}")
            videos_a_reproducir = obtener_videos(categoria)

            if videos_a_reproducir:
                reproducir_videos(videos_a_reproducir)
            else:
                print(f"No hay suficientes videos en {categoria}")

        print("\n🔄 Reiniciando ciclo de reproducción...\n")
        time.sleep(5)  # Pausa antes de reiniciar

if __name__ == "__main__":
    main()
