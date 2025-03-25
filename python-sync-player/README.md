# Sync Player

Este documento contiene las instrucciones para hacer las pruebas de funcionamiento del Sync Player con Python..

## Sync Player Simple

Este programa reproduce dos videos de forma sincronizada. Se deben cumplir manualmente los siguientes requicitos.

- La Raspberry Pi Lider tendrá como nombre de usuario pione
- La Raspberry Pi Seguidora tendrá como nombre de usuaro pitwo
- Los videos A y B deben estar en el directorio /home/pione/videos/videoA.mp4
- Ambas Raspberry Pi deberan estár conectadas a la misma red WiFi, esta red no requiere acceso a internet.
- El programa Lider debe modificarse para apuntar a la ip de la follower.
- Se usa MPV, un reproductor de video externo, el cual debe instalarse prevamente a ejecutar los programas
    ```
    sudo apt update
    sudo apt install -y mpv
    ```
- Instalar socat para sincronizar los reproductores
    ```
    sudo apt install -y socat
    ```

Se recomienda clonar el repositorio con github.

## Uso

- El el programa "simple" sirve para probar la existencia de los archivos, las rutas, los nombres de usuario y la paridad en la misma red loca.
- El programa coordinated sirve para comprobar la viavilidad de IPC
- El programa Multi Cordinated es el reproductor manual sincronizado en loop que puede quedar funcionando en una instalación no automatizada.
