from src.core.config import ALLOWED_CHAT_IDS, ADMIN_CHAT_IDS

# ==========================================
# SEGURIDAD Y CONTROL DE ACCESO
# ==========================================

def es_usuario_permitido(user_id: int) -> bool:
    """Valida si el user_id tiene permiso de usar el sistema."""
    if not ALLOWED_CHAT_IDS:
        return True # Si no hay lista blanca, todo el mundo pasa.
    return user_id in ALLOWED_CHAT_IDS

def es_admin(user_id: int) -> bool:
    """Valida si el user_id tiene privilegios de administrador maestro."""
    if not ADMIN_CHAT_IDS:
        return False # Restricción estricta: Si no está explícitamente nombrado, NO es admin.
    return user_id in ADMIN_CHAT_IDS
