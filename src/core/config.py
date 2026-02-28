import os
from dotenv import load_dotenv

# Cargamos las variables de entorno una sola vez para toda la aplicación
load_dotenv()

# ==========================================
# CONFIGURACIONES GLOBALES DEL AGENTE
# ==========================================

# Variables de presentación
AGENT_NAME = os.getenv("AGENT_NAME", "Agente B2B Elite")
USER_TITLE = os.getenv("USER_TITLE", "Jefe")

# Token de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Seguridad: Lista Blanca de Chats
allowed_chats_env = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in allowed_chats_env.split(",")] if allowed_chats_env else []

# Modelo LLM Elegido
LLM_MODEL = os.getenv("LLM_MODEL", "gemini").lower()
