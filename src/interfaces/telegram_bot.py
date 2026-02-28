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

async def enviar_resultados(chat_id: int, context: ContextTypes.DEFAULT_TYPE, mensaje_estado, resultado: dict):
    """
    Función auxiliar para procesar la salida estandarizada del Agente Service.
    Envia el texto y adjunta los Excels si los hubo.
    """
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=mensaje_estado.message_id,
        text=resultado["respuesta_texto"]
    )
    for excel in resultado.get("archivos_excel", []):
        nombre = StorageService.obtener_nombre_archivo(excel)
        await context.bot.send_message(chat_id=chat_id, text=f"📁 Adjuntando: {nombre}...")
        
        # Le pedimos al storage service que nos dé el archivo
        with StorageService.obtener_stream_archivo(excel) as document:
            await context.bot.send_document(chat_id=chat_id, document=document)
            
    # Limpiamos la carpeta después de enviar todo para que búsquedas fallidas futuras no envíen estos archivos
    if resultado.get("archivos_excel"):
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
        # Aquí Telegram SOLO funciona como mensajero. Delega el procesamiento al servicio del Agente.
        resultado = await procesar_mensaje_agente(texto_usuario, str(chat_id))
        await enviar_resultados(chat_id, context, mensaje_estado, resultado)
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
        await enviar_resultados(chat_id, context, mensaje_estado, resultado)
        
    except Exception as e:
        print(f"❌ Error al procesar audio: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"❌ Ocurrió un error al intentar procesar o transcribir el audio: {str(e)}"
        )

# ==========================================
# ARRANQUE DEL BOT
# ==========================================
def main():
    """Función principal que enciende el servidor de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ CRÍTICO: No encontré TELEGRAM_BOT_TOKEN en el archivo .env")
        return
        
    print("🤖 Encendiendo Agente y conectando con Telegram...")
    # Construimos la aplicación de Telegram
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registramos nuestros "manejadores" (handlers)
    app.add_handler(CommandHandler("start", start_command))
    
    # Esto le dice que capture TODOS los mensajes de texto que no sean comandos especiales
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    # Novedad: Capturar NOTAS DE VOZ (y audios grabados) y enrutarlos a nuestro Whisper
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, manejar_audio))
    
    print("✅ ¡Bot listo y escuchando mensajes (y Audios!) en Telegram! (Presiona Ctrl+C para detener)")
    
    # Arrancamos el ciclo infinito de "Long Polling"
    app.run_polling()

if __name__ == "__main__":
    main()
