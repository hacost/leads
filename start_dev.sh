#!/bin/bash

# ==============================================================================
# Bastion Core - Local Development Launcher
# ==============================================================================
# Este script lanza los 3 servicios principales en segundo plano para facilitar
# el desarrollo local. 
#
# USO:
# ./start_dev.sh
#
# Puedes detener todos los servicios simplemente presionando Ctrl+C.
# ==============================================================================

# Colores para la salida en consola
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando Entorno de Desarrollo de Bastión Core ===${NC}\n"

# Deshabilitar buffering de Python para logs en tiempo real
export PYTHONUNBUFFERED=1

# 0. Limpieza agresiva de procesos huérfanos
echo -e "${YELLOW}Limpiando procesos anteriores...${NC}"
pkill -9 -f "main.py" 2>/dev/null
pkill -9 -f "scraper_worker" 2>/dev/null
pkill -9 -f "uvicorn" 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# 0.5 Preparar directorio y marca de tiempo para archivos
mkdir -p logs
TS=$(date +"%Y-%m-%d_%H-%M-%S")

# Definir el binario de python de la venv para estabilidad absoluta
PY="./.venv/bin/python3"

# 1. Iniciar el Bot de Telegram (Polling Interface)
echo -e "${YELLOW}[1/4] Iniciando Bot de Telegram...${NC}"
$PY -u main.py > "logs/[$TS] [BOT].log" 2>&1 &
BOT_PID=$!

# 2. Iniciar el Scraper Worker (Async Background Jobs)
echo -e "${YELLOW}[2/4] Iniciando Scraper Worker (Cola asíncrona)...${NC}"
$PY -u -m src.application.batch_jobs.scraper_worker > "logs/[$TS] [WORKER].log" 2>&1 &
WORKER_PID=$!

# 3. Iniciar la API de FastAPI (Backend)
echo -e "${YELLOW}[3/4] Iniciando FastAPI Backend en el puerto 8000...${NC}"
./.venv/bin/uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000 > "logs/[$TS] [API].log" 2>&1 &
API_PID=$!

# 4. Iniciar el Frontend (Next.js Dashboard) con Binding Universal (Local + Red)
echo -e "${YELLOW}[4/4] Iniciando Next.js Frontend...${NC}"

# Detectar IP local en macOS para la presentación profesional
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

# Binding a 0.0.0.0 garantiza acceso desde localhost Y red simultáneamente
(cd frontend && npm run dev -- -H 0.0.0.0 2>&1 | while read -r line; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [FRONTEND] $line"
done > "../logs/[$TS] [FRONTEND].log") &
FRONTEND_PID=$!

# Esperar un breve momento para que los puertos se abran antes del banner
sleep 2

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}🚀 BASTION CORE DASHBOARD LISTO PARA DESARROLLO${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "💻 ${BLUE}Local:${NC}      http://localhost:3000"
echo -e "🌐 ${BLUE}Red:${NC}        http://$LOCAL_IP:3000"
echo -e "------------------------------------------------------"
echo -e "📡 ${BLUE}API Local:${NC}  http://localhost:8000"
echo -e "📡 ${BLUE}API Red:${NC}    http://$LOCAL_IP:8000"
echo -e "${GREEN}======================================================${NC}"
echo -e "${RED}Presiona Ctrl+C para detener TODOS los servicios.${NC}\n"
echo -e "${RED}Presiona Ctrl+C para detener TODOS los servicios.${NC}\n"

# Función para atrapar Ctrl+C y matar los procesos directos e hijos
cleanup() {
    printf "\n${RED}Deteniendo todos los servicios de desarrollo...${NC}\n"
    
    # Intentar matar educadamente (SIGTERM)
    kill -TERM $BOT_PID $WORKER_PID $API_PID $FRONTEND_PID 2>/dev/null
    
    # Matar cualquier proceso hijo rezagado (especialmente de node/next)
    pkill -P $$ 2>/dev/null
    
    # Esperar un momento y forzar (SIGKILL) si siguen vivos
    sleep 1
    kill -9 $BOT_PID $WORKER_PID $API_PID $FRONTEND_PID 2>/dev/null
    
    printf "¡Hasta luego!\n"
    # Salir forzosamente para liberar la terminal
    exit 0
}

# Configurar el "trap" para SIGINT (Ctrl+C) o SIGTERM
trap cleanup SIGINT SIGTERM

# Esperar indefinidamente para que el script no termine y mantenga los hijos vivos
wait
