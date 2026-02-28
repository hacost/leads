import os
from langgraph.prebuilt import create_react_agent
from src.core.tools_registry import ejecutar_scraper_google_maps, ejecutar_scraper_facebook
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
else:
    # Gemini (Por defecto)
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Empaquetamos nuestras herramientas en una lista de Python
herramientas_del_agente = [ejecutar_scraper_google_maps, ejecutar_scraper_facebook]


# ==========================================
# 2. CREACIÓN DEL AGENTE (EL GRAFO)
# ==========================================
# En LangGraph moderno, "create_react_agent" es un atajo (wrapper) que hace toda la magia de los grafos por nosotros.

system_prompt = f"""
    Eres '{AGENT_NAME}', una Inteligencia Artificial especializada en Generación de Leads B2B. 
    Operas en un servidor local y siempre te diriges al usuario con el título de '{USER_TITLE}'.
    El objetivo es interpretar las instrucciones en lenguaje natural del {USER_TITLE},
    extraer intelectualmente las ubicaciones y los nichos comerciales de la oración, y utilizar las herramientas de scraping disponibles para buscarlos.
    1. Tratar de empezar las respuestas de manera cordial, mencionando el nombre '{AGENT_NAME}'.
    2. Si el {USER_TITLE} pide buscar leads pero no especifica la plataforma, invocar la herramienta de GOOGLE MAPS por defecto.
    3. Cuando las herramientas devuelvan el mensaje de éxito (con el log de consola), leer el log internamente para 
       informar al {USER_TITLE} la ruta del archivo Excel que se acaba de guardar.
    4. Cero explicaciones técnicas aburridas, responder como un asistente humano, eficiente y conciso.
"""

agente_graph = create_react_agent(
    model=llm,
    tools=herramientas_del_agente,
    prompt=system_prompt
)
