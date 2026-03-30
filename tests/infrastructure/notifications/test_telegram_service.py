import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.notifications.telegram_service import TelegramService

@pytest.mark.asyncio
class TestTelegramService:
    """
    Suite para validar el nuevo servicio profesional de notificaciones.
    EXPECTED: RED (o error de colección) hasta que se implemente el servicio.
    """
    
    async def test_notificar_resultado_agente_edita_mensaje_existente(self):
            
        mock_bot = AsyncMock()
        mock_resultado = {"respuesta_texto": "Hola Amo"}
        mock_mensaje_estado = MagicMock()
        mock_mensaje_estado.message_id = 123
        
        await TelegramService.notificar_resultado_agente(
            bot=mock_bot,
            chat_id="8209526798",
            mensaje_estado=mock_mensaje_estado,
            resultado=mock_resultado
        )
        
        # Debe llamar a edit_message_text con los parámetros correctos
        mock_bot.edit_message_text.assert_called_once_with(
            chat_id="8209526798",
            message_id=123,
            text="Hola Amo",
            parse_mode=None
        )
