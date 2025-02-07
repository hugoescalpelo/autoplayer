import os
import random
import subprocess
import time

# Ruta base donde están las 10 carpetas de categorías
BASE_PATH = "/ruta/a/tus/videos"  # <- Modifica esto con la ruta real

def obtener_videos(categoria_path):
    """ Obtiene videos de la carpeta de imágenes y textos """
    texto_path = os.path.join(categoria_path, "textos")
    imagenes_path = os.path.join(categoria_path, "imagenes")

    # Obtener lista de videos
    videos_texto = [os.path.join(texto_path, v) for v in os.listdir(texto_path) if v.endswith(('.mp4', '.avi', '.mkv'))]
    videos_imagenes = [os.path.join(imagenes_path, v) for v in os.listdir(imagenes_path) if v.endswith(('.mp4', '.avi', '.mkv'))]

    if not videos_texto or len(videos_imagenes) < 3:
        return []

    # Elegir aleatoriamente los videos
    video_texto = random.choice(videos_texto)
    videos_imagenes = random.sample(videos_imagenes, 3)

    return [video_texto] + videos_imagenes

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
