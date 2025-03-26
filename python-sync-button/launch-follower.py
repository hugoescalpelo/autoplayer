#!/bin/bash

# Ruta del proyecto
PROJECT_DIR="/home/pitwo/Documents/GitHub/autoplayer/python-sync-button"

# Ejecutar cada programa en segundo plano y redirigir salida
echo "🚀 Iniciando follower-buttons..."
python3 "$PROJECT_DIR/follower-buttons.py" > /tmp/follower-buttons.log 2>&1 &

echo "🚀 Iniciando follower-receiver..."
python3 "$PROJECT_DIR/follower-receiver.py" > /tmp/follower-receiver.log 2>&1 &

echo "🚀 Iniciando follower-sync..."
python3 "$PROJECT_DIR/follower-sync.py" > /tmp/follower-sync.log 2>&1 &

echo "✅ Todos los procesos del follower han sido iniciados."
