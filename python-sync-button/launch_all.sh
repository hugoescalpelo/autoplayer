#!/bin/bash
echo "🚀 Iniciando todos los procesos en Leader..."

cd /home/user/Documents/GitHub/autoplayer/python-sync-button/

echo "🎬 Ejecutando leader_sync.py"
python3 leader_sync.py &

sleep 2

echo "📡 Ejecutando leader_receiver.py"
python3 leader_receiver.py &

echo "🎛️ Ejecutando leader-buttons.py"
python3 leader-buttons.py &
