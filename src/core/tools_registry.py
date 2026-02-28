import subprocess
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig

# ==========================================
# 1. REGISTRO DE HERRAMIENTAS (TOOLS)
# ==========================================
# Aquí viven las herramientas (Tools) aisladas del Agente Principal.
# El Agente ya no sabe *cómo* se ejecutan los scrapers en la consola (subprocess), 
# solo sabe que estas herramientas existen y las manda a llamar.

@tool
def ejecutar_scraper_google_maps(zonas: str, categorias: str, config: RunnableConfig) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads, negocios, tiendas o empresas 
    usando Google Maps. 
    Acepta dos parámetros como string:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    print(f"\n[🤖 AGENTE EJECUTANDO HERRAMIENTA] -> Google Maps scraper.")
    print(f"   ► Parámetros recibidos del LLM: Zonas={zonas} | Categorias={categorias}")
    
    # Construimos el comando igual que si lo escribiéramos en la terminal con uv run
    comando = [
        "uv", "run", "src/scrapers/scraper.py", 
        "--zones", zonas, 
        "--categories", categorias,
        "--output-dir", f"leads/session_{thread_id}"
    ]
    
    # subprocess.run ejecuta el comando de forma "aislada" en la consola del sistema.
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        return f"Éxito: El scraper de Maps finalizó. Log final de consola:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando scraper de Maps: {e.stderr}"

@tool
def ejecutar_scraper_facebook(zonas: str, categorias: str, config: RunnableConfig) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads o negocios ESPECÍFICAMENTE en Facebook,
    o cuando pida buscar directamente perfiles de redes sociales.
    Acepta dos parámetros:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    """
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    print(f"\n[🤖 AGENTE EJECUTANDO HERRAMIENTA] -> Facebook scraper.")
    print(f"   ► Parámetros recibidos del LLM: Zonas={zonas} | Categorias={categorias}")
    
    comando = [
        "uv", "run", "src/scrapers/facebook_search_scraper.py", 
        "--zones", zonas, 
        "--categories", categorias,
        "--output-dir", f"leads/session_{thread_id}"
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        return f"Éxito: El scraper de Facebook finalizó. Log final de consola:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando scraper de Facebook: {e.stderr}"
