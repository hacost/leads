import os
from langgraph.prebuilt import create_react_agent
from src.core.tools_registry import ejecutar_scraper_google_maps, ejecutar_scraper_facebook, gestionar_recordatorio
from src.core.config import LLM_MODEL, AGENT_NAME, USER_TITLE

# ==========================================
# 1. DEFINICIÓN DEL "CEREBRO" (LLM)
# ==========================================

if LLM_MODEL == "claude":
    # Si quieres usar Claude, asegúrate de tener ANTHROPIC_API_KEY en tu .env
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model_name="claude-3-5-sonnet-latest", temperature=0)
elif LLM_MODEL == "gpt":
    # Si quieres usar ChatGPT, asegúrate de tener OPENAI_API_KEY en tu .env
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
elif LLM_MODEL == "groq":
    # Groq Llama 3.3 (Muy rápido y gratuito)
    # Requiere GROQ_API_KEY en .env
    from langchain_groq import ChatGroq
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
else:
    # Gemini (Por defecto)
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

# Empaquetamos nuestras herramientas en una lista de Python
herramientas_del_agente = [ejecutar_scraper_google_maps, ejecutar_scraper_facebook, gestionar_recordatorio]


# ==========================================
# 2. CREACIÓN DEL AGENTE (EL GRAFO)
# ==========================================
# En LangGraph moderno, "create_react_agent" es un atajo (wrapper) que hace toda la magia de los grafos por nosotros.

system_prompt = f"""
    Eres '{AGENT_NAME}', una Inteligencia Artificial especializada en Generación de Leads B2B. 
    Operas en un servidor local y siempre te diriges al usuario con el título de '{USER_TITLE}'.
    El objetivo es interpretar las instrucciones en lenguaje natural del {USER_TITLE}.

    Tus habilidades principales:
    A) Extraer ubicaciones y nichos, y usar herramientas de scraping para buscarlos en vivo.
    B) Crear, listar o borrar RECORDATORIOS (alertas autónomas) para ejecutar tareas de forma recurrente.

    Reglas de Comportamiento:
    1. Tratar de empezar las respuestas de manera cordial, mencionando el nombre '{AGENT_NAME}'.
    2. Si el {USER_TITLE} pide buscar leads pero no especifica la plataforma, invoca la herramienta de GOOGLE MAPS.
    3. Si el {USER_TITLE} te pide "avisarle", "recordarle", o hacer algo "todos los días/lunes/etc.", invoca la herramienta `gestionar_recordatorio` con la acción 'agendar'. Tú debes deducir y crear la expresión CRON válida de 5 campos.
    4. Cuando las herramientas devuelvan éxito (ej. búsqueda de leads), usa esa información para responder cortésmente y decir la ruta del archivo generado.
    5. Cero explicaciones técnicas aburridas. Responde como un asistente humano, eficiente y conciso.
"""

agente_graph = create_react_agent(
    model=llm,
    tools=herramientas_del_agente,
    prompt=system_prompt
)
