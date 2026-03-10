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
        "uv", "run", "python", "-m", "src.scrapers.scraper", 
        "--zones", zonas, 
        "--categories", categorias,
        "--session-id", thread_id
    ]
    
    # subprocess.run ejecuta el comando de forma "aislada" en la consola del sistema.
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        # Checking if zero rows were added to the DB, meaning no new results. Focus on the actual output.
        if "0 new rows added" in resultado.stdout or "Extracted: " not in resultado.stdout:
            return f"BÚSQUEDA FALLIDA: NO SE ENCONTRÓ NINGÚN RESULTADO válido para {categorias} en {zonas}. Por favor, informa al usuario que no obtuviste resultados. NO se generó ningún archivo."
        else:
            return f"Éxito. INSTRUCCIÓN ESTRICTA: Escribe ÚNICAMENTE '¡Hola {config.get('configurable', {}).get('thread_id', 'Amo')}! He terminado de buscar.' y debajo enlista SOLAMENTE LAS RUTAS de los archivos Excel generados con viñetas (bullet points) basándote en este log. ESTÁ PROHIBIDO mencionar la base de datos (leads.db), carpetas internas o dar explicaciones técnicas largas:\n{resultado.stdout[-500:]}"
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
        "uv", "run", "python", "-m", "src.scrapers.facebook_search_scraper", 
        "--zones", zonas, 
        "--categories", categorias,
        "--session-id", thread_id
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        return f"Éxito: El scraper de Facebook finalizó. Log final de consola:\n{resultado.stdout[-500:]}"
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando scraper de Facebook: {e.stderr}"

@tool
def gestionar_recordatorio(accion: str, config: RunnableConfig, cron_expression: str = "", prompt_task: str = "", alerta_id: int | str = 0) -> str:
    """
    Usa esta herramienta cuando el usuario te pida PROGRAMAR o AGENDAR una búsqueda o resumen recurrente, 
    o cuando pida LISTAR o BORRAR un recordatorio previamente configurado.
    
    Acepta los siguientes parámetros:
    - accion: 'agendar', 'listar' o 'borrar'.
    - cron_expression: (Solo para agendar) Formato CRON de 5 asteriscos validado según el deseo del usuario. Ejemplo: "0 9 * * 1" (Lunes a las 9 am).
    - prompt_task: (Solo para agendar) Las instrucciones exactas que debe ejecutar el bot cuando se despierte la alerta, escrito como si el usuario lo estuviera pidiendo en ese momento, ej. "Busca ferreterías en Monterrey".
    - alerta_id: (Solo para borrar) El ID de la alerta que se quiere eliminar.
    """
    from src.services.scheduler_service import SchedulerService
    from src.services.storage_service import StorageService
    
    chat_id = config.get("configurable", {}).get("thread_id", "default")
    print(f"\n[🤖 AGENTE EJECUTANDO HERRAMIENTA] -> Gestión de Alertas (Acción: {accion}).")
    
    if accion == "agendar":
        try:
            nuevo_id = SchedulerService.agendar_alerta(chat_id, cron_expression, prompt_task)
            return f"Éxito: Alerta programada con ID {nuevo_id}. CRON: {cron_expression}. Tarea: {prompt_task}."
        except Exception as e:
            return f"Error al agendar alerta: Revisar si el formato CRON ({cron_expression}) es válido. Detalle: {str(e)}"
    
    elif accion == "listar":
        alertas = StorageService.obtener_alertas(chat_id)
        if not alertas:
            return "No hay alertas programadas activas para este usuario."
        respuesta = "Alertas activas para este usuario:\n"
        for a in alertas:
            respuesta += f"- ID: {a['id']} | CRON: {a['cron_expression']} | TAREA: {a['prompt_task']}\n"
        return respuesta
        
    elif accion == "borrar":
        # Safe casting against the issue where LLM sends string '0' or '1'
        try:
            alerta_id = int(alerta_id)
        except ValueError:
            return "Error: alerta_id debe ser un número entero válido."
            
        if alerta_id <= 0:
            return "Error: Para borrar se requiere un alerta_id válido numérico mayor a 0."
        exito = SchedulerService.eliminar_alerta(alerta_id, chat_id)
        if exito:
            return f"Éxito: La alerta con ID {alerta_id} ha sido borrada."
        else:
            return f"Error: No se encontró alerta con ID {alerta_id} o no pertenece a este usuario."
            
    else:
        return "Error: 'accion' debe ser 'agendar', 'listar' o 'borrar'."

