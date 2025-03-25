# Sync Player

Este documento contiene las instrucciones para hacer las pruebas de funcionamiento del Sync Player con Python..

## Sync Player Simple

Este programa reproduce dos videos de forma sincronizada. Se deben cumplir manualmente los siguientes requicitos.

- La Raspberry Pi Lider tendrá como nombre de usuario pione
- La Raspberry Pi Seguidora tendrá como nombre de usuaro pitwo
- Los videos A y B deben estar en el directorio /home/pione/videos/videoA.mp4
- Ambas Raspberry Pi deberan estár conectadas a la misma red WiFi, esta red no requiere acceso a internet.
- Se usa MPV, un reproductor de video externo, el cual debe instalarse prevamente a ejecutar los programas
    ```
    sudo apt update
    sudo apt install -y mpv
    ```
- Instalar el simulador de teclas presionadas
    ```
    sudo apt install xdotool
    ```

Se recomienda clonar el repositorio con github.

