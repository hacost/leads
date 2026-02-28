import os
import glob
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_core.messages import HumanMessage

# Graph Import
from src.agents.agent import agente_graph

load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Reduce logging noise from standard HTTP layers
logging.getLogger("httpx").setLevel(logging.WARNING)

# ==========================================
# ACCESS CONTROL
# ==========================================
# Read allowed Telegram Chat IDs from environment variables.
# If empty, validation passes for any ID.
allowed_chats_env = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(cid.strip()) for cid in allowed_chats_env.split(",")] if allowed_chats_env else []

def es_usuario_permitido(chat_id: int) -> bool:
    """Validates if the provided chat_id has permission to access the bot."""
    if not ALLOWED_CHAT_IDS:
        return True # Default to open access if no whitelist is specified.
    return chat_id in ALLOWED_CHAT_IDS

# ==========================================
# TELEGRAM EVENT HANDLERS
# ==========================================

# Load prompt context
agent_name = os.getenv("AGENT_NAME", "B2B Agent")
user_title = os.getenv("USER_TITLE", "User")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command execution in Telegram."""
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        print(f"[AUTH DENIED] Invalid Chat ID attempt: {chat_id}")
        await update.message.reply_text(f"🛑 Access Denied. Chat ID ({chat_id}) is not authorized.")
        return
    
    bienvenida = (
        f"¡Hola {user_title}! Soy '{agent_name}'.\n\n"
        "Puedo buscar empresas en Google Maps o Facebook.\n"
        "Solo dime algo como: 'Búscame dentistas en San Pedro Garza Garcia'."
    )
    await update.message.reply_text(bienvenida)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Triggered when a user sends a text message.
    Connects the Telegram input overlay with the LangGraph execution layer.
    """
    texto_usuario = update.message.text
    chat_id = update.message.chat_id
    
    if not es_usuario_permitido(chat_id):
        print(f"[AUTH DENIED] Chat ID: {chat_id} | Input: {texto_usuario}")
        await update.message.reply_text(f"🛑 Access Denied.")
        return
        
    # Console Logging
    print(f"\n[USER INPUT]: {texto_usuario}")

    # 1. Update UI Status
    mensaje_estado = await update.message.reply_text("🤔 Processing request...")
    
    try:
        # 2. Invoke LangGraph Execution
        # Pass the human message and associate the current chat_id to maintain conversational state.
        config = {"configurable": {"thread_id": str(chat_id)}}
        
        # Graph invocation
        respuesta_grafo = agente_graph.invoke(
            {"messages": [HumanMessage(content=texto_usuario)]},
            config=config
        )
        
        import json
        
        ultimo_mensaje = respuesta_grafo["messages"][-1]
        respuesta_cruda = ultimo_mensaje.content
        
        # Display token usage stats if provided by the model provider metadata
        if hasattr(ultimo_mensaje, 'usage_metadata') and ultimo_mensaje.usage_metadata:
            tokens = ultimo_mensaje.usage_metadata
            in_tokens = tokens.get('input_tokens', 0)
            out_tokens = tokens.get('output_tokens', 0)
            total_tokens = tokens.get('total_tokens', 0)
            print(f"   [USAGE STATS] Input Tokens: {in_tokens} | Output Tokens: {out_tokens} | Total: {total_tokens}")
        
        # Normalize LLM Response Format
        # Extract text strictly as string to mitigate variations in tool/JSON serialization logic.
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
        # 3. Deliver text payload
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=respuesta_final_texto
        )
        
        # Output Log Console
        print(f"[AGENT RESPONSE]: {respuesta_final_texto}")

        # 4. File Output Delivery
        # Identify if any scraping action generated export files utilizing LangChain Tool Calls
        se_uso_scraper = any(
            hasattr(msg, 'tool_calls') and msg.tool_calls 
            for msg in respuesta_grafo["messages"]
        )

        if se_uso_scraper:
            print("   -> [INFO] Scraper tool identified in action queue. Fetching relevant files directory...")
            # Fetch directory by established session pattern
            specific_dir = f"leads/session_{chat_id}"
            if os.path.exists(specific_dir):
                excel_files = glob.glob(os.path.join(specific_dir, '*.xlsx'))
                
                # Upload successfully generated datasets
                for excel in excel_files:
                    await update.message.reply_text(f"📁 Attaching result: {os.path.basename(excel)}...")
                    with open(excel, 'rb') as document:
                        await context.bot.send_document(chat_id=chat_id, document=document)
            else:
                print(f"   -> [WARNING] Output directory not found: {specific_dir}")
        else:
            print("   -> [INFO] Interaction did not require file dataset dispatch.")
                    
    except Exception as e:
        # Error fallback UI update
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=mensaje_estado.message_id,
            text=f"Encountered an execution error: {str(e)}"
        )

# ==========================================
# BOT DAEMON INITIALIZATION
# ==========================================
def main():
    """Initializes and runs the main Telegram daemon server."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[CRITICAL] TELEGRAM_BOT_TOKEN environment variable is undefined.")
        return
        
    print("[SYSTEM] Starting Agent UI interface daemon...")
    
    # Init application engine
    app = Application.builder().token(token).build()
    
    # Map command routers
    app.add_handler(CommandHandler("start", start_command))
    
    # Map message routers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    print("[SYSTEM] Instance online. Telegram Polling bound...")
    
    # Arrancamos el ciclo infinito de "Long Polling"
    app.run_polling()

if __name__ == "__main__":
    main()
