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

# 1. Iniciar el Bot de Telegram (Polling Worker)
echo -e "${YELLOW}[1/3] Iniciando Bot de Telegram...${NC}"
uv run main.py &
BOT_PID=$!

# 2. Iniciar la API de FastAPI (Backend)
echo -e "${YELLOW}[2/3] Iniciando FastAPI Backend en el puerto 8000...${NC}"
uv run uvicorn src.presentation.api.main:app --port 8000 --reload &
API_PID=$!

# 3. Iniciar el Frontend (Next.js Dashboard)
echo -e "${YELLOW}[3/3] Iniciando Next.js Frontend en el puerto 3000...${NC}"
cd frontend && npm run dev &
FRONTEND_PID=$!

echo -e "\n${GREEN}Todos los servicios han sido iniciados correctamente.${NC}"
echo -e "${BLUE}API URL:${NC}      http://localhost:8000"
echo -e "${BLUE}Dashboard:${NC}    http://localhost:3000"
echo -e "${RED}Presiona Ctrl+C para detener TODOS los servicios.${NC}\n"

# Función para atrapar Ctrl+C y matar los procesos directos e hijos
cleanup() {
    printf "\n${RED}Deteniendo todos los servicios de desarrollo...${NC}\n"
    
    # Enviar señal de terminación a los procesos
    kill -TERM $BOT_PID $API_PID $FRONTEND_PID 2>/dev/null
    
    # Esperar silenciosamente a que terminen de apagar (FastAPI y Next.js)
    wait $BOT_PID $API_PID $FRONTEND_PID 2>/dev/null
    
    printf "¡Hasta luego!\n"
    exit 0
}

# Configurar el "trap" para SIGINT (Ctrl+C) o SIGTERM
trap cleanup SIGINT SIGTERM

# Esperar indefinidamente para que el script no termine y mantenga los hijos vivos
wait
