import os
import subprocess
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# ==========================================
# 1. TOOL DEFINITIONS
# ==========================================
# Tools are Python functions exposed to the LLM.
# The @tool decorator registers the function as a callable tool for LangGraph.
# Docstrings are strictly used by the LLM to understand context, required parameters, and execution triggers.

@tool
def ejecutar_scraper_google_maps(zonas: str, categorias: str, thread_id: str) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads, negocios, tiendas o empresas 
    usando Google Maps. 
    Acepta tres parámetros como string:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    - thread_id: El identificador único de la conversación (proporcionado automáticamente).
    """
    print(f"\n[INFO] Executing Tool: Google Maps Scraper")
    print(f"       Parameters: Zones={zonas} | Categories={categorias}")
    
    # Build command for subprocess execution
    comando = [
        "uv", "run", "src/scrapers/scraper.py", 
        "--zones", zonas, 
        "--categories", categorias,
        "--output-dir", f"leads/session_{thread_id}"
    ]
    
    # Execute the command in an isolated subprocess.
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        # Return tail of standard output to the LLM to confirm successful execution and file paths.
        return f"Success: Google Maps scraper completed. Final console output:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        # Return standard error to the LLM for context on failures.
        return f"Error executing Google Maps scraper: {e.stderr}"

@tool
def ejecutar_scraper_facebook(zonas: str, categorias: str, thread_id: str) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads o negocios ESPECÍFICAMENTE en Facebook,
    o cuando pida buscar directamente perfiles de redes sociales.
    Acepta tres parámetros:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    - thread_id: El identificador único de la conversación (proporcionado automáticamente).
    """
    print(f"\n[INFO] Executing Tool: Facebook Scraper")
    print(f"       Parameters: Zones={zonas} | Categories={categorias}")
    
    comando = [
        "uv", "run", "src/scrapers/facebook_search_scraper.py", 
        "--zones", zonas, 
        "--categories", categorias,
        "--output-dir", f"leads/session_{thread_id}"
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        return f"Success: Facebook scraper completed. Final console output:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        return f"Error executing Facebook scraper: {e.stderr}"


# ==========================================
# 2. LLM CONFIGURATION
# ==========================================
import os
from dotenv import load_dotenv
load_dotenv()

# Select LLM back-end
modelo_elegido = os.getenv("LLM_MODEL", "gemini").lower()

if modelo_elegido == "claude":
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model_name="claude-3-5-sonnet-latest", temperature=0)
elif modelo_elegido == "gpt":
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
else:
    # Default to Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Register defined tools
herramientas_del_agente = [ejecutar_scraper_google_maps, ejecutar_scraper_facebook]


# ==========================================
# 3. AGENT GRAPH INITIALIZATION
# ==========================================
# create_react_agent is used to orchestrate the ReAct (Reasoning and Acting) execution loop.
# It handles dynamic tool dispatching.

# Load environment personalization
agent_name = os.getenv("AGENT_NAME", "B2B Agent")
user_title = os.getenv("USER_TITLE", "User")

system_prompt = f"""
    Eres '{agent_name}', una Inteligencia Artificial especializada en Generación de Leads B2B. 
    Ejecutas tareas desde un servidor local y te comunicas formalmente utilizando el título '{user_title}'.
    El objetivo principal es interpretar requerimientos en lenguaje natural,
    extraer ubicaciones y nichos comerciales, y emplear las herramientas de scraping disponibles para su búsqueda.
    1. Iniciar las interacciones de manera cordial, mencionando el identificador '{agent_name}'.
    2. Si no se especifica explícitamente la plataforma de búsqueda en la instrucción, invocar la herramienta de GOOGLE MAPS por defecto.
    3. Al confirmar el éxito de la ejecución (vía lectura de logs de consola),
       informar al usuario la ruta exacta del archivo Excel generado.
    4. Mantener un estilo de comunicación profesional, directo, eficiente y conciso, evitando tecnicismos innecesarios.
"""

agente_graph = create_react_agent(
    model=llm,
    tools=herramientas_del_agente,
    prompt=system_prompt
)
