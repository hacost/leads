"""
Suite TDD completa para src/presentation/telegram_bot/telegram_bot.py

ESTADO ESPERADO: ROJO — los tests verifican el comportamiento objetivo:
- El bot solo envía el texto de la respuesta del agente.
- El bot NO llama a enviar_resultados_al_chat (o ésta ya no busca Excels).
- El bot NO intenta enviar documentos de forma síncrona.

ESTRATEGIA DE MOCKS:
- Mockear `Update` y `Context` de python-telegram-bot.
- Mockear `procesar_mensaje_agente` para controlar el retorno.
- Mockear `es_usuario_permitido` para evitar lógica de seguridad en tests unitarios.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Mocking modules that might cause slow imports or side effects
with patch("src.application.ai_agents.agent_service.agente_graph", MagicMock()):
    from src.presentation.telegram_bot.telegram_bot import manejar_mensaje, manejar_audio


def _make_mock_update(text="hola", chat_id=12345):
    update = MagicMock()
    update.message.text = text
    update.message.chat_id = chat_id
    update.message.reply_text = AsyncMock()
    return update


def _make_mock_context():
    context = MagicMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_document = AsyncMock()
    return context


@pytest.mark.asyncio
class TestTelegramBotManejo:

    @patch("src.presentation.telegram_bot.telegram_bot.es_usuario_permitido", return_value=True)
    @patch("src.presentation.telegram_bot.telegram_bot.procesar_mensaje_agente")
    async def test_manejar_mensaje_solo_responde_texto_del_agente(self, mock_procesar, mock_permitido):
        """
        VERDE: Verifica que el bot solo edite el mensaje con la respuesta de texto.
        """
        update = _make_mock_update("Busca dentistas")
        context = _make_mock_context()
        
        # Simulamos que el agente responde que encoló el trabajo
        mock_procesar.return_value = {
            "respuesta_texto": "¡Hola! He encolado tu búsqueda de dentistas."
        }

        # Ejecutamos manejar_mensaje
        await manejar_mensaje(update, context)

        # Verificamos que se llamó al agente
        mock_procesar.assert_called_once_with("Busca dentistas", "12345")

        # Verificamos que se editó el mensaje de estado con la respuesta
        context.bot.edit_message_text.assert_called_once()
        args = context.bot.edit_message_text.call_args[1]
        assert "dentistas" in args["text"]
        
        # EL bot NO debe enviar documentos
        context.bot.send_document.assert_not_called()
            
    @patch("src.presentation.telegram_bot.telegram_bot.es_usuario_permitido", return_value=True)
    @patch("src.presentation.telegram_bot.telegram_bot.procesar_mensaje_agente")
    async def test_manejar_mensaje_no_busca_ni_envia_excels(self, mock_procesar, mock_permitido):
        """
        VERDE: Aunque el agente simule respuesta de scraper, el bot ya no tiene
        lógica para enviar archivos ni dependencia de StorageService.
        """
        update = _make_mock_update("Busca plomeros")
        context = _make_mock_context()
        
        mock_procesar.return_value = {
            "respuesta_texto": "Buscando plomeros..."
        }

        await manejar_mensaje(update, context)

        # Assert: NO debe llamar a send_document
        context.bot.send_document.assert_not_called()

    @patch("src.presentation.telegram_bot.telegram_bot.es_usuario_permitido", return_value=False)
    async def test_manejar_mensaje_deniega_acceso_si_no_permitido(self, mock_permitido):
        """Verifica que se bloquee a usuarios no autorizados (comportamiento actual que debe persistir)."""
        update = _make_mock_update()
        context = _make_mock_context()

        await manejar_mensaje(update, context)

        update.message.reply_text.assert_called_once()
        assert "Acceso Denegado" in update.message.reply_text.call_args[0][0]
