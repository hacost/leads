import os
import subprocess
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# ==========================================
# 1. DEFINICIÓN DE HERRAMIENTAS (TOOLS)
# ==========================================
# Las herramientas son funciones de Python que le enseñamos al LLM a usar.
# El decorador @tool convierte esta función normal en una "herramienta" que Gemini puede entender e invocar.
# El "docstring" (el texto entre comillas triples) es CRÍTICO: El modelo lee este texto
# para entender CUÁNDO debe usar esta herramienta, QUÉ hace y CÓMO debe pasarle los parámetros.

@tool
def ejecutar_scraper_google_maps(zonas: str, categorias: str) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads, negocios, tiendas o empresas 
    usando Google Maps. 
    Acepta dos parámetros como string:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    """
    print(f"\n[🤖 AGENTE EJECUTANDO HERRAMIENTA] -> Google Maps scraper.")
    print(f"   ► Parámetros recibidos del LLM: Zonas={zonas} | Categorias={categorias}")
    
    # Construimos el comando igual que si lo escribiéramos en la terminal con uv run
    comando = [
        "uv", "run", "src/scrapers/scraper.py", 
        "--zones", zonas, 
        "--categories", categorias
    ]
    
    # subprocess.run ejecuta el comando de forma "aislada" en la consola de tu computadora.
    # capture_output=True significa que el Agente "lee" todo lo que el script imprime en la consola.
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        # Le regresamos a Gemini los últimos caracteres del log de consola para que sepa si terminó con éxito y dónde se guardó.
        return f"Éxito: El scraper de Maps finalizó. Log final de consola:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        # Si la consola truena, Gemini recibe el error y puede decidir disculparse o reintentar.
        return f"Error ejecutando scraper de Maps: {e.stderr}"

@tool
def ejecutar_scraper_facebook(zonas: str, categorias: str) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads o negocios ESPECÍFICAMENTE en Facebook,
    o cuando pida buscar directamente perfiles de redes sociales.
    Acepta dos parámetros:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    """
    print(f"\n[🤖 AGENTE EJECUTANDO HERRAMIENTA] -> Facebook scraper.")
    print(f"   ► Parámetros recibidos del LLM: Zonas={zonas} | Categorias={categorias}")
    
    comando = [
        "uv", "run", "src/scrapers/facebook_search_scraper.py", 
        "--zones", zonas, 
        "--categories", categorias
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        return f"Éxito: El scraper de Facebook finalizó. Log final de consola:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando scraper de Facebook: {e.stderr}"


# ==========================================
# 2. DEFINICIÓN DEL "CEREBRO" (LLM)
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
# 3. CREACIÓN DEL AGENTE (EL GRAFO)
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
    Vives en un servidor local y siempre te diriges a tu usuario con el título de '{user_title}'.
    Tu trabajo es interpretar las órdenes en lenguaje natural del {user_title},
    extraer intelectualmente las ubicaciones y los nichos comerciales de la oración, y utilizar tus herramientas de scraping para buscarlos.
    1. Trata de empezar tus respuestas de manera cordial, mencionando tu nombre '{agent_name}'.
    2. Si el {user_title} pide buscar leads pero no especifica la plataforma, invoca la herramienta de GOOGLE MAPS por defecto.
    3. Cuando las herramientas te devuelvan el mensaje de éxito (con el log de consola), lee el log internamente para 
       informar al {user_title} la ruta del archivo Excel que se acaba de guardar ("leads/2026.../leads_micro.xlsx").
    4. Cero explicaciones técnicas aburridas, responde como un asistente humano, leal, eficiente y conciso.
"""

agente_graph = create_react_agent(
    model=llm,
    tools=herramientas_del_agente,
    prompt=system_prompt
)
