#!/bin/bash

# Ruta del proyecto
PROJECT_DIR="/home/pione/Documents/GitHub/autoplayer/python-sync-button"

# Activar entorno virtual si tienes uno (opcional)
# source $PROJECT_DIR/venv/bin/activate

# Ejecutar cada programa en segundo plano y redirigir salida
echo "🚀 Iniciando leader-buttons..."
python3 "$PROJECT_DIR/leader-buttons.py" > /tmp/leader-buttons.log 2>&1 &

echo "🚀 Iniciando leader-receiver..."
python3 "$PROJECT_DIR/leader-receiver.py" > /tmp/leader-receiver.log 2>&1 &

echo "🚀 Iniciando leader-sync..."
python3 "$PROJECT_DIR/leader-sync.py" > /tmp/leader-sync.log 2>&1 &

echo "✅ Todos los procesos del leader han sido iniciados."
