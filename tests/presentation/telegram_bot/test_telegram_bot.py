import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update
from telegram.ext import ContextTypes

# Mockeamos dependencias pesadas
with patch("src.presentation.telegram_bot.telegram_bot.on_startup", MagicMock()):
    from src.presentation.telegram_bot.telegram_bot import manejar_mensaje

@pytest.mark.asyncio
class TestTelegramBot:
    """
    Suite para el Bot. Busca validar que delegue la respuesta al TelegramService.
    EXPECTED: RED (actualmente usa context.bot.edit_message_text directamente).
    """

    @patch("src.presentation.telegram_bot.telegram_bot.es_usuario_permitido")
    @patch("src.presentation.telegram_bot.telegram_bot.procesar_mensaje_agente")
    @patch("src.presentation.telegram_bot.telegram_bot.TelegramService")
    async def test_manejar_mensaje_delega_al_servicio_de_notificaciones(self, mock_service, mock_agente, mock_permiso):
        """Test para asegurar que la lógica de respuesta está centralizada en el servicio profesional."""
        mock_permiso.return_value = True
        mock_agente.return_value = {"respuesta_texto": "Respuesta Pro"}
        
        # Simulación de objetos de telegram.ext
        update = MagicMock(spec=Update)
        update.message.text = "Hola"
        update.message.chat_id = 12345
        update.message.reply_text = AsyncMock()
        
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = AsyncMock()
        
        # El bot envía el mensaje inicial de estado
        mock_estado = AsyncMock()
        update.message.reply_text.return_value = mock_estado
        
        # EJECUCIÓN
        await manejar_mensaje(update, context)
        
        # VERIFICACIÓN (TDD RED): El código actual llama a edit_message_text
        # Queremos que llame al servicio en su lugar.
        mock_service.notificar_resultado_agente.assert_called_once()
