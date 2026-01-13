#!/bin/bash

# ==========================================
# SKATE 3 PROXY - CORE SERVER (Backend)
# ==========================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export LD_LIBRARY_PATH="$DIR":$LD_LIBRARY_PATH

MODE="local"
TARGET_IP="162.244.53.174"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --mode) MODE="$2"; shift ;;
        --ip) TARGET_IP="$2"; shift ;;
    esac
    shift
done

# Limpieza de procesos anteriores
pkill -f "socat" 2>/dev/null
pkill -f "Skateboard3Server.Host" 2>/dev/null

echo "----------------------------------------"
echo " SKATE 3 PROXY | MODO: $MODE"
echo "----------------------------------------"

if [ "$MODE" == "local" ]; then
    echo ">> Iniciando Servidor .NET..."
    # Ejecución directa. Como el lanzador ya es root, no necesitamos sudo aquí
    ./Skateboard3Server.Host

else
    # MODO ONLINE
    if ! command -v socat &> /dev/null; then
        echo "Error: socat no instalado"
        exit 1
    fi
    
    echo ">> Iniciando Puente a $TARGET_IP..."
    
    # Socat en modo verbose (-v)
    socat -v TCP-LISTEN:80,fork,bind=127.0.0.1 TCP:$TARGET_IP:80 &
    PID1=$!
    socat -v TCP-LISTEN:443,fork,bind=127.0.0.1 TCP:$TARGET_IP:443 &
    PID2=$!
    
    wait $PID1 $PID2
fi
