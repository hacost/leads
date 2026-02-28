import os

# ==========================================
# SEGURIDAD Y CONTROL DE ACCESO
# ==========================================
# Leemos los IDs permitidos desde el .env.
allowed_chats_env = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in allowed_chats_env.split(",")] if allowed_chats_env else []

def es_usuario_permitido(user_id: int) -> bool:
    """Valida si el user_id tiene permiso de usar el sistema."""
    if not ALLOWED_CHAT_IDS:
        return True # Si no hay lista blanca, todo el mundo pasa.
    return user_id in ALLOWED_CHAT_IDS
