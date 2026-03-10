import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Importamos las capacidades desde nuestras capas limpias (Clean Architecture)
from src.core.security import es_usuario_permitido
from src.services.audio_service import transcribir_audio
from src.services.agent_service import procesar_mensaje_agente
from src.services.storage_service import StorageService
from src.services.scheduler_service import SchedulerService
from src.core.config import AGENT_NAME, USER_TITLE, TELEGRAM_BOT_TOKEN

# Habilitamos el registro de errores (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ==========================================
# LÓGICA DE TELEGRAM
# ==========================================

async def enviar_mensaje_acceso_denegado(update: Update, chat_id: int):
    """Maneja y responde a los intentos de acceso no autorizados."""
    print(f"⚠️ INTENTO DE ACCESO BLOQUEADO. Chat ID Invalido: {chat_id}")
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
        "Solo dime algo como: 'Búscame dentistas en San Pedro Garza Garcia'."
    )
    await update.message.reply_text(bienvenida)

async def enviar_resultados_al_chat(bot, chat_id: int, mensaje_estado, resultado: dict):
    """
    Función auxiliar para procesar la salida estandarizada del Agente Service.
    Envia el texto y adjunta los Excels si los hubo.
    Lógica centralizada para respetar el principio DRY.
    """
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mensaje_estado.message_id,
        text=resultado["respuesta_texto"]
    )
    # Solo procesa lógica de archivos si el Agente ejecutó la herramienta de scraping
    if resultado.get("se_uso_scraper", False):
        archivos = resultado.get("archivos_excel", [])
        for excel in archivos:
            nombre = StorageService.obtener_nombre_archivo(excel)
            await bot.send_message(chat_id=chat_id, text=f"📁 Adjuntando: {nombre}...")
            
            # Le pedimos al storage service que nos dé el archivo
            with StorageService.obtener_stream_archivo(excel) as document:
                await bot.send_document(chat_id=chat_id, document=document)
                
        # Limpiamos la carpeta después de enviar todo para que búsquedas fallidas futuras no envíen estos archivos
        if archivos:
            StorageService.eliminar_sesion(str(chat_id))

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Esta función se dispara cada vez que un usuario escribe un mensaje en el chat.
    Aquí Telegram SOLO funciona como mensajero. Delega el procesamiento al servicio del Agente.
    """
    texto_usuario = update.message.text
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        await enviar_mensaje_acceso_denegado(update, chat_id)
        return
        
    # Se imprime en la consola del sistema el mensaje del usuario
    print(f"\n[👤 {USER_TITLE}]: {texto_usuario}")
    
    # 1. Avisamos que el Agente está pensando...
    mensaje_estado = await update.message.reply_text("🤔 Analizando petición y ejecutando herramientas...")
    
    try:
        resultado = await procesar_mensaje_agente(texto_usuario, str(chat_id))
        await enviar_resultados_al_chat(context.bot, chat_id, mensaje_estado, resultado)
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"Lo siento, mis circuitos fallaron: {str(e)}"
        )

async def manejar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Escucha una nota de voz de Telegram, la descarga temporalmente y la manda 
    al Audio_Service para transcribirla, y luego al Agent_Service para procesarla.
    """
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        await enviar_mensaje_acceso_denegado(update, chat_id)
        return
        
    mensaje_estado = await update.message.reply_text("🎙️ Escuchando y transcribiendo nota de voz...")
    
    try:
        voice_file_id = update.message.voice.file_id
        telegram_file = await context.bot.get_file(voice_file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_path = temp_audio.name
            
        await telegram_file.download_to_drive(temp_path)
        print(f"   -> [INFO] Audio descargado temporalmente a {temp_path}")
        
        # Delegamos la responsabilidad de STT a la capa de Servicios
        texto_usuario = await transcribir_audio(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        print(f"\n[🎙️ {USER_TITLE} (Voz)]: {texto_usuario}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"🗣️ Transcripción: '{texto_usuario}'\n\n🤔 Analizando petición y ejecutando herramientas..."
        )
        
        # Re-usamos la misma lógica del Agente que se usa para texto
        resultado = await procesar_mensaje_agente(texto_usuario, str(chat_id))
        await enviar_resultados_al_chat(context.bot, chat_id, mensaje_estado, resultado)
        
    except Exception as e:
        print(f"❌ Error al procesar audio: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"❌ Ocurrió un error al intentar procesar o transcribir el audio: {str(e)}"
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
    from src.services.scheduler_service import SchedulerService
    SchedulerService.iniciar(app)

def main():
    """Función principal que enciende el servidor de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ CRÍTICO: No encontré TELEGRAM_BOT_TOKEN en el archivo .env")
        return
        
    print("🤖 Encendiendo Agente y conectando con Telegram...")
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
    
    print("✅ ¡Bot listo y escuchando mensajes (y Audios!) en Telegram! (Presiona Ctrl+C para detener)")
    
    # Arrancamos el ciclo infinito de "Long Polling"
    app.run_polling()

if __name__ == "__main__":
    main()
