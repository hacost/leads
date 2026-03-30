import logging
from telegram import Bot, Message

logger = logging.getLogger(__name__)

class TelegramService:
    @staticmethod
    async def notificar_resultado_agente(bot: Bot, chat_id: str, mensaje_estado: Message, resultado: dict):
        """
        Centraliza la entrega de respuestas del Agente (Bastioncito) al usuario vía Telegram.
        Actualiza el mensaje de estado previo ("Pensando...") con la respuesta final.
        """
        respuesta_texto = resultado.get("respuesta_texto", "Lo siento, no pude generar una respuesta.")
        
        try:
            logger.info(f"📤 [TelegramService] Enviando respuesta a Chat {chat_id}...")
            
            # Intentamos editar el mensaje de estado previo
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=mensaje_estado.message_id,
                text=respuesta_texto,
                parse_mode=None # Opcional: podrías usar "Markdown" si el agente devuelve MD limpio
            )
            logger.info("✅ [TelegramService] Mensaje actualizado exitosamente.")
            
        except Exception as e:
            logger.error(f"❌ [TelegramService] Error al editar mensaje: {str(e)}")
            # Fallback: Si falla la edición, enviamos un mensaje nuevo
            try:
                await bot.send_message(chat_id=chat_id, text=respuesta_texto)
            except Exception as e2:
                logger.error(f"❌ [TelegramService] Error crítico total: {str(e2)}")
