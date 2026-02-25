import os
import glob
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_core.messages import HumanMessage

# Importamos nuestro "cerebro" (el Grafo de LangGraph)
from src.agents.agent import agente_graph

load_dotenv()

# ==========================================
# LÓGICA DE TELEGRAM
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start en Telegram."""
    bienvenida = (
        "¡Hola! Soy el Agente Elite de Generación de Leads de Bastion.\n\n"
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
        
        # Extraemos el último mensaje generado por el Agente (la respuesta final en texto)
        respuesta_final_texto = respuesta_grafo["messages"][-1].content
        
        # 3. Enviamos el texto de respuesta al usuario
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=respuesta_final_texto
        )
        
        # 4. Magia de entrega: Buscamos si el Agente generó un Excel
        # Vamos a buscar la carpeta más reciente dentro de `leads/`
        # Solo enviaremos archivos si en la respuesta de Gemini se menciona la palabra 'éxito' o 'leads' 
        # (puedes ajustar esta lógica).
        list_of_dirs = glob.glob('leads/*')
        if list_of_dirs:
            latest_dir = max(list_of_dirs, key=os.path.getctime)
            excel_files = glob.glob(os.path.join(latest_dir, '*.xlsx'))
            
            # Subimos cada archivo Excel recién creado al chat de Telegram
            for excel in excel_files:
                await update.message.reply_text(f"📁 Adjuntando: {os.path.basename(excel)}...")
                with open(excel, 'rb') as document:
                    await context.bot.send_document(chat_id=chat_id, document=document)
                    
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
