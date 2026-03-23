import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Importamos las capacidades desde nuestras capas limpias (Clean Architecture)
from src.core.security import es_usuario_permitido
from src.infrastructure.audio.audio_service import transcribir_audio
from src.application.ai_agents.agent_service import procesar_mensaje_agente
from src.application.batch_jobs.scheduler_service import SchedulerService
from src.core.config import AGENT_NAME, USER_TITLE, TELEGRAM_BOT_TOKEN

from src.core.logging_config import setup_logging
# Configuración global de logs del Bot
logger = setup_logging("BOT")

# ==========================================
# LÓGICA DE TELEGRAM
# ==========================================

async def enviar_mensaje_acceso_denegado(update: Update, chat_id: int):
    """Maneja y responde a los intentos de acceso no autorizados."""
    logger.warning(f"⚠️ INTENTO DE ACCESO BLOQUEADO. Chat ID Invalido: {chat_id}")
    await update.message.reply_text(f"🛑 Acceso Denegado. El Chat ID ({chat_id}) no está en la lista blanca del {USER_TITLE}.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start en Telegram."""
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        await enviar_mensaje_acceso_denegado(update, chat_id)
        return
    
    bienvenida = (
        f"¡Hola {USER_TITLE}! Soy '{AGENT_NAME}'.\n\n"
        "Puedo buscar empresas en Google Maps o Facebook.\n"
        "Solo dime algo como: 'Búscame dentistas en Monterrey'."
    )
    await update.message.reply_text(bienvenida)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Captura los mensajes de texto, los envía al Agente y muestra su respuesta.
    El envío de archivos de scraping es ahora asíncrono (vía Worker).
    """
    texto_usuario = update.message.text
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        await enviar_mensaje_acceso_denegado(update, chat_id)
        return
        
    logger.info(f"[👤 {USER_TITLE}]: {texto_usuario}")
    mensaje_estado = await update.message.reply_text("🤔 Pensando...")
    
    try:
        resultado = await procesar_mensaje_agente(texto_usuario, str(chat_id))
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=resultado["respuesta_texto"]
        )
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"Lo siento, ocurrió un error: {str(e)}"
        )

async def manejar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Escucha una nota de voz, la transcribe y delega el procesamiento al Agente.
    """
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        await enviar_mensaje_acceso_denegado(update, chat_id)
        return
        
    mensaje_estado = await update.message.reply_text("🎙️ Escuchando y transcribiendo...")
    
    try:
        voice_file_id = update.message.voice.file_id
        telegram_file = await context.bot.get_file(voice_file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_path = temp_audio.name
            
        await telegram_file.download_to_drive(temp_path)
        
        # Transcripción (STT)
        texto_usuario = await transcribir_audio(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        logger.info(f"[🎙️ {USER_TITLE} (Voz)]: {texto_usuario}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"🗣️ Transcripción: '{texto_usuario}'\n\n🤔 Pensando..."
        )
        
        # Procesamiento con Agente
        resultado = await procesar_mensaje_agente(texto_usuario, str(chat_id))
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=resultado["respuesta_texto"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error al procesar audio: {str(e)}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"❌ Error al procesar audio: {str(e)}"
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los errores globales para evitar tracebacks rojos que asusten al usuario."""
    import telegram
    if isinstance(context.error, telegram.error.NetworkError):
        logging.warning("⚠️ [Red] Micro-corte o error 502 de Telegram. El bot está diseñado para ignorarlo y reconectarse silenciosamente en segundo plano.")
    else:
        logging.error("❌ Ocurrió un error inesperado en Telegram:", exc_info=context.error)

# ==========================================
# ARRANQUE DEL BOT
# ==========================================

async def on_startup(app: Application):
    """Se ejecuta una vez que el Application de Telegram arranca su event loop."""
    from src.application.batch_jobs.scheduler_service import SchedulerService
    SchedulerService.iniciar(app)

def main():
    """Función principal que enciende el servidor de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ CRÍTICO: No encontré TELEGRAM_BOT_TOKEN en el archivo .env")
        return
        
    logger.info("🤖 Encendiendo Agente y conectando con Telegram...")
    # Construimos la aplicación de Telegram y registramos el hook de inicio
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(on_startup).build()
    
    # Registramos nuestros "manejadores" (handlers)
    app.add_handler(CommandHandler("start", start_command))
    
    # Esto le dice que capture TODOS los mensajes de texto que no sean comandos especiales
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    # Novedad: Capturar NOTAS DE VOZ (y audios grabados) y enrutarlos a nuestro Whisper
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, manejar_audio))
    
    # Manejador Global de Errores para que los fallos de Red de Telegram no inunden tu terminal
    app.add_error_handler(error_handler)
    
    logger.info("✅ ¡Bot listo y escuchando mensajes (y Audios!) en Telegram! (Presiona Ctrl+C para detener)")
    
    # Arrancamos el ciclo infinito de "Long Polling"
    app.run_polling()

if __name__ == "__main__":
    main()
