# autoplayer
Este repositorio contiene código para un autoplayer simple por gerarquía de carpetas.

## Instrucciones
- Comprueba que python esté instalado.
    ```
    python3 --version
    ```
- Instala `mvp`, un reproductor ligero en python.
    ```
    sudo apt update && sudo apt install mpv -y
    ```
- Edita crontab.
    ```
    crontab -e
    ```
- Agrega la siguiente linea a crontab para que se inicie el programa al arrancar el sistema.
    ```
    @reboot python3 /ruta/donde/guardaste/auto_player.py &
    ```


