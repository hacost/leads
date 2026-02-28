import os
from src.core.tools_registry import ejecutar_scraper_google_maps, ejecutar_scraper_facebook

# ==========================================
# 1. DEFINICIÓN DEL "CEREBRO" (LLM)
# ==========================================
# Leemos el archivo .env para cargar las llaves secretas
import os
from dotenv import load_dotenv
load_dotenv()

# Magia Multi-Modelo: Leemos qué IA quieres usar. Si no pones nada, usa Gemini.
modelo_elegido = os.getenv("LLM_MODEL", "gemini").lower()

if modelo_elegido == "claude":
    # Si quieres usar Claude, asegúrate de tener ANTHROPIC_API_KEY en tu .env
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model_name="claude-3-5-sonnet-latest", temperature=0)
elif modelo_elegido == "gpt":
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
# Toma el cerebro (llm) y le da acceso a las manos (las tools de la lista).
# Internamente construye un Grafo con un ciclo que dice:
#   1. Llamar al LLM (El LLM ve si necesita usar una tool o si ya puede responder).
#   2. Si decide usar una tool, llama al Nodo de Herramientas.
#   3. El nodo de Herramientas ejecuta la función de Python (ej. subprocess) y devuelve el texto.
#   4. Le regresa el texto al LLM. El ciclo inicia de nuevo hasta que el LLM decide que ya tiene la respuesta.

# Leemos las variables de personalización
agent_name = os.getenv("AGENT_NAME", "Agente Elite B2B")
user_title = os.getenv("USER_TITLE", "CEO")

system_prompt = f"""
    Eres '{agent_name}', una Inteligencia Artificial especializada en Generación de Leads B2B. 
    Operas en un servidor local y siempre te diriges al usuario con el título de '{user_title}'.
    El objetivo es interpretar las instrucciones en lenguaje natural del {user_title},
    extraer intelectualmente las ubicaciones y los nichos comerciales de la oración, y utilizar las herramientas de scraping disponibles para buscarlos.
    1. Tratar de empezar las respuestas de manera cordial, mencionando el nombre '{agent_name}'.
    2. Si el {user_title} pide buscar leads pero no especifica la plataforma, invocar la herramienta de GOOGLE MAPS por defecto.
    3. Cuando las herramientas devuelvan el mensaje de éxito (con el log de consola), leer el log internamente para 
       informar al {user_title} la ruta del archivo Excel que se acaba de guardar.
    4. Cero explicaciones técnicas aburridas, responder como un asistente humano, eficiente y conciso.
"""

agente_graph = create_react_agent(
    model=llm,
    tools=herramientas_del_agente,
    prompt=system_prompt
)
