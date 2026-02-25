import os
import glob
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_core.messages import HumanMessage

# Importamos nuestro "cerebro" (el Grafo de LangGraph)
from src.agents.agent import agente_graph

load_dotenv()

# Habilitamos el registro de errores (Logging) para ver qué pasa "tras bambalinas" en Telegram
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Reducimos el ruido de las peticiones HTTP normales
logging.getLogger("httpx").setLevel(logging.WARNING)

# ==========================================
# SEGURIDAD Y CONTROL DE ACCESO
# ==========================================
# Leemos los IDs de Telegram permitidos desde el .env.
# Si está vacío, cualquiera puede usar el bot. Si tiene IDs, solo ellos podrán.
# Ejemplo en el .env: ALLOWED_CHAT_IDS="1234567,9876543"
allowed_chats_env = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in allowed_chats_env.split(",")] if allowed_chats_env else []

def es_usuario_permitido(chat_id: int) -> bool:
    """Valida si el chat_id tiene permiso de usar el bot."""
    if not ALLOWED_CHAT_IDS:
        return True # Si no hay lista blanca, todo el mundo pasa.
    return chat_id in ALLOWED_CHAT_IDS

# ==========================================
# LÓGICA DE TELEGRAM
# ==========================================

# Leemos las opciones del .env
agent_name = os.getenv("AGENT_NAME", "Agente B2B Elite")
user_title = os.getenv("USER_TITLE", "Jefe")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start en Telegram."""
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        print(f"⚠️ INTENTO DE ACCESO BLOQUEADO. Chat ID Invalido: {chat_id}")
        await update.message.reply_text(f"🛑 Acceso Denegado. No te conozco. Tu Chat ID es: {chat_id}, compartelo con mi {user_title} para que te de acceso")
        return
    
    bienvenida = (
        f"¡Hola {user_title}! Soy '{agent_name}'.\n\n"
        "Puedo buscar empresas en Google Maps o Facebook.\n"
        "Solo dime algo como: 'Búscame dentistas en San Pedro Garza Garcia'."
    )
    await update.message.reply_text(bienvenida)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Esta función se dispara cada vez que tú o tu hijo escriben un mensaje en el chat.
    Aquí conectamos Telegram con LangGraph.
    """
    texto_usuario = update.message.text
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        print(f"⚠️ INTENTO DE USO BLOQUEADO. Chat ID: {chat_id} | Mensaje: {texto_usuario}")
        await update.message.reply_text(f"🛑 Acceso Denegado. Tu Chat ID ({chat_id}) no está en la lista blanca de mi {user_title}.")
        return
        
    # Imprimimos en la consola de tu computadora lo que dice el usuario
    print(f"\n[👤 {user_title}]: {texto_usuario}")

    # 1. Avisamos que el Agente está pensando...
    mensaje_estado = await update.message.reply_text("🤔 Analizando petición y ejecutando herramientas...")
    
    try:
        # 2. Invocamos a LangGraph
        # Le pasamos el mensaje del usuario como un 'HumanMessage'.
        # El config 'thread_id' es para que el Agente recuerde el contexto de la conversación.
        config = {"configurable": {"thread_id": str(chat_id)}}
        
        # '.invoke' ejecuta todo el ciclo del grafo (LLM -> Tool -> LLM) hasta tener la respuesta final
        respuesta_grafo = agente_graph.invoke(
            {"messages": [HumanMessage(content=texto_usuario)]},
            config=config
        )
        
        import json
        
        # Extraemos el último mensaje generado por el Agente (la respuesta final en texto)
        respuesta_cruda = respuesta_grafo["messages"][-1].content
        
        # A veces Gemini devuelve el texto como una lista de bloques JSON o un string en formato JSON raro.
        # Vamos a limpiarlo para que sea siempre texto humano puro.
        if isinstance(respuesta_cruda, list):
            fragmentos = [item.get("text", "") for item in respuesta_cruda if isinstance(item, dict) and "text" in item]
            respuesta_final_texto = "\n".join(fragmentos)
        elif isinstance(respuesta_cruda, str) and respuesta_cruda.strip().startswith("[{") and "text" in respuesta_cruda:
            try:
                datos_json = json.loads(respuesta_cruda)
                fragmentos = [item.get("text", "") for item in datos_json if isinstance(item, dict) and "text" in item]
                respuesta_final_texto = "\n".join(fragmentos)
            except Exception:
                respuesta_final_texto = str(respuesta_cruda)
        else:
            respuesta_final_texto = str(respuesta_cruda)
        # 3. Enviamos el texto de respuesta al usuario
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=respuesta_final_texto
        )
        
        # Imprimimos la respuesta en tu consola
        print(f"[🤖 {agent_name}]: {respuesta_final_texto}")

        # 4. Magia de entrega: Buscamos si el Agente generó un Excel
        # IMPORTANTE: Solo buscaremos y enviaremos archivos si el Agente realmente ejecutó un scraper.
        # ¿Cómo lo sabemos? Buscando si entre los mensajes de respuesta hay alguna 'tool_call' (llamada a herramienta).
        se_uso_scraper = any(
            hasattr(msg, 'tool_calls') and msg.tool_calls 
            for msg in respuesta_grafo["messages"]
        )

        if se_uso_scraper:
            print("   -> 📦 Detecté que se ejecutó un scraper. Buscando archivos Excel recientes...")
            list_of_dirs = glob.glob('leads/*')
            if list_of_dirs:
                latest_dir = max(list_of_dirs, key=os.path.getctime)
                excel_files = glob.glob(os.path.join(latest_dir, '*.xlsx'))
                
                # Subimos cada archivo Excel recién creado al chat de Telegram
                for excel in excel_files:
                    await update.message.reply_text(f"📁 Adjuntando: {os.path.basename(excel)}...")
                    with open(excel, 'rb') as document:
                        await context.bot.send_document(chat_id=chat_id, document=document)
        else:
            print("   -> 💬 Solo fue una charla normal. No busco archivos Excel.")
                    
    except Exception as e:
        # Si algo explota (llaves malas, error de internet), avisamos amablemente.
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"Lo siento, mis circuitos fallaron: {str(e)}"
        )

# ==========================================
# ARRANQUE DEL BOT
# ==========================================
def main():
    """Función principal que enciende el servidor de Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ CRÍTICO: No encontré TELEGRAM_BOT_TOKEN en el archivo .env")
        return
        
    print("🤖 Encendiendo Agente y conectando con Telegram...")
    
    # Construimos la aplicación de Telegram
    app = Application.builder().token(token).build()
    
    # Registramos nuestros "manejadores" (handlers)
    app.add_handler(CommandHandler("start", start_command))
    # Esto le dice que capture TODOS los mensajes de texto que no sean comandos especiales
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    print("✅ ¡Bot listo y escuchando mensajes en Telegram! (Presiona Ctrl+C para detener)")
    
    # Arrancamos el ciclo infinito de "Long Polling"
    app.run_polling()

if __name__ == "__main__":
    main()
