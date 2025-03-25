#!/bin/bash
echo "🚀 Iniciando todos los procesos en Leader..."

cd /home/pione/Documents/GitHub/autoplayer/python-sync-button/

echo "🎬 Ejecutando leader-sync.py"
python3 leader-sync.py &

sleep 2

echo "📡 Ejecutando leader-receiver.py"
python3 leader-receiver.py &

echo "🎛️ Ejecutando leader-buttons.py"
python3 leader-buttons.py &
