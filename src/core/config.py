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

# Seguridad: Lista de Administradores
admin_chats_env = os.getenv("ADMIN_CHAT_IDS", "")
ADMIN_CHAT_IDS = [int(cid.strip()) for cid in admin_chats_env.split(",")] if admin_chats_env else []

# Modelo LLM Elegido
LLM_MODEL = os.getenv("LLM_MODEL", "groq").lower()

# JWT Secret para la API FastAPI
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-bastion-core")

# CORS: Orígenes permitidos (para desarrollo y producción)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS = [o.strip() for o in allowed_origins_env.split(",")] if allowed_origins_env else ["http://localhost:3000"]
