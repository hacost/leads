import json
from langchain_core.messages import HumanMessage
from src.agents.agent import agente_graph
from src.core.config import AGENT_NAME

async def procesar_mensaje_agente(texto_usuario: str, session_id: str) -> dict:
    """
    Envía el mensaje en texto puro al Agente y procesa la interacción de LangGraph.
    Desacoplado de la UI: devuelve un diccionario con el texto de respuesta y las rutas de los archivos generados.
    """
    config = {"configurable": {"thread_id": str(session_id)}}
    
    respuesta_grafo = agente_graph.invoke(
        {"messages": [HumanMessage(content=texto_usuario)]},
        config=config
    )
    
    ultimo_mensaje = respuesta_grafo["messages"][-1]
    respuesta_cruda = ultimo_mensaje.content
    
    # Imprimir tokens usados si están disponibles
    if hasattr(ultimo_mensaje, 'usage_metadata') and ultimo_mensaje.usage_metadata:
        tokens = ultimo_mensaje.usage_metadata
        in_tokens = tokens.get('input_tokens', 0)
        out_tokens = tokens.get('output_tokens', 0)
        total_tokens = tokens.get('total_tokens', 0)
        print(f"   [🪙 TOKENS GEMINI] Entrada: {in_tokens} | Salida: {out_tokens} | Usados esta vez: {total_tokens}")
    
    # Limpiamos salidas extrañas de JSON
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
        
    print(f"[🤖 {AGENT_NAME}]: {respuesta_final_texto}")

    # Verificar si el Agente invocó alguna de nuestras herramientas de scraping
    se_uso_scraper = any(
        hasattr(msg, 'tool_calls') and msg.tool_calls and any(tc['name'].startswith('ejecutar_scraper') for tc in msg.tool_calls)
        for msg in respuesta_grafo["messages"]
    )

    archivos_generados = []
    if se_uso_scraper:
        print("   -> 📦 Detecté que se ejecutó un scraper. Buscando archivos Excel recientes...")
        from src.services.storage_service import buscar_excels_de_usuario
        archivos_generados = buscar_excels_de_usuario(session_id)
        if not archivos_generados:
            print(f"   -> ❌ No se encontró la carpeta esperada para la sesión: {session_id}")
    else:
        print("   -> 💬 Solo fue una charla normal. No busco archivos Excel.")

    return {
        "respuesta_texto": respuesta_final_texto,
        "archivos_excel": archivos_generados
    }
