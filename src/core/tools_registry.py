from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from src.infrastructure.database.storage_service import StorageService
import logging

logger = logging.getLogger(__name__)

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
    owner_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"[🤖 AGENTE ENCOLANDO TRABAJO] -> Google Maps scraper.")
    
    lista_zonas = [z.strip() for z in zonas.split(";") if z.strip()]
    lista_cats = [c.strip() for c in categorias.split(";") if c.strip()]
    
    jobs_creados = []
    zonas_invalidas = []
    
    for cat_name in lista_cats:
        for zona_name in lista_zonas:
            # Validar contra ciudades maestras (Gaps Auditoría Sprint 2.5)
            city_data = StorageService.get_city_by_name(zona_name)
            if not city_data:
                logger.warning(f"   ⚠️ [Validación] Ciudad '{zona_name}' no encontrada en la DB maestra.")
                zonas_invalidas.append(zona_name)
                continue
                
            city_id = city_data['id']
            cat_id = StorageService.get_or_create_category(cat_name, owner_id)
            
            # Encolamos el trabajo
            job_id = StorageService.create_job(cat_id, city_id, owner_id)
            jobs_creados.append(str(job_id))
    
    if not jobs_creados:
        if zonas_invalidas:
            return f"❌ Lo siento, las zonas solicitadas ({', '.join(zonas_invalidas)}) no son zonas operativas permitidas actualmente. Por favor, intenta con Monterrey, San Pedro, CDMX o Puebla."
        return "No se pudieron crear los trabajos de búsqueda. Verifica los parámetros."
        
    respuesta = f"✅ ¡Entendido! He agendado {len(jobs_creados)} búsqueda(s) de extracción (Job IDs: {', '.join(jobs_creados)})."
    if zonas_invalidas:
        respuesta += f" (Nota: las zonas '{', '.join(zonas_invalidas)}' fueron ignoradas por no ser zonas operativas permitidas)."
    
    return respuesta + " Te enviaré los resultados por este chat en cuanto el proceso termine en segundo plano. ¿Hay algo más en lo que pueda ayudarte mientras tanto?"

@tool
def ejecutar_scraper_facebook(zonas: str, categorias: str, config: RunnableConfig) -> str:
    """
    Usa esta herramienta cuando el usuario pida buscar leads o negocios ESPECÍFICAMENTE en Facebook.
    Acepta dos parámetros:
    - zonas: Las ciudades o municipios separados por punto y coma (ej. "Monterrey; San Pedro").
    - categorias: El giro del negocio separado por punto y coma (ej. "Dentistas; Plomeros").
    """
    owner_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"[🤖 AGENTE ENCOLANDO TRABAJO] -> Facebook scraper.")
    
    lista_zonas = [z.strip() for z in zonas.split(";") if z.strip()]
    lista_cats = [c.strip() for c in categorias.split(";") if c.strip()]
    
    jobs_creados = []
    for cat_name in lista_cats:
        for zona_name in lista_zonas:
            city_id = StorageService.get_or_create_city(zona_name)
            cat_id = StorageService.get_or_create_category(cat_name, owner_id)
            job_id = StorageService.create_job(cat_id, city_id, owner_id)
            jobs_creados.append(str(job_id))
            
    return f"✅ He encolado {len(jobs_creados)} búsqueda(s) en Facebook. Recibirás los archivos aquí automáticamente."

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
    from src.application.batch_jobs.scheduler_service import SchedulerService
    from src.infrastructure.database.storage_service import StorageService
    
    chat_id = config.get("configurable", {}).get("thread_id", "default")
    logger.info(f"[🤖 AGENTE EJECUTANDO HERRAMIENTA] -> Gestión de Alertas (Acción: {accion}).")
    
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

