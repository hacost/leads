import json
from langchain_core.messages import HumanMessage
from src.application.ai_agents.agent import agente_graph
from src.core.config import AGENT_NAME

async def procesar_mensaje_agente(texto_usuario: str, session_id: str) -> dict:
    """
    Envía el mensaje en texto puro al Agente y procesa la interacción de LangGraph.
    Devuelve un diccionario simple con el texto de respuesta.
    """
    config = {"configurable": {"thread_id": str(session_id)}}
    
    from datetime import datetime
    import pytz
    tz = pytz.timezone('America/Mexico_City')
    fecha_hora_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    texto_con_contexto = (
        f"[CONTEXTO DEL SISTEMA: La hora actual es {fecha_hora_str} en {tz.zone}. "
        "Por favor saluda apropiadamente. Atiende el siguiente mensaje: ]\n\n"
        f"Mensaje del Usuario: {texto_usuario}"
    )
    
    respuesta_grafo = agente_graph.invoke(
        {"messages": [HumanMessage(content=texto_con_contexto)]},
        config=config
    )
    
    ultimo_mensaje = respuesta_grafo["messages"][-1]
    respuesta_cruda = ultimo_mensaje.content
    
    # Registro de uso de tokens
    if hasattr(ultimo_mensaje, 'usage_metadata') and ultimo_mensaje.usage_metadata:
        tokens = ultimo_mensaje.usage_metadata
        print(f"   [🪙 TOKENS] Entrada: {tokens.get('input_tokens',0)} | Salida: {tokens.get('output_tokens',0)}")
    
    # Limpieza de la respuesta (manejo de formatos extraños de Gemini/LangGraph)
    if isinstance(respuesta_cruda, list):
        fragmentos = [item.get("text", "") for item in respuesta_cruda if isinstance(item, dict) and "text" in item]
        respuesta_texto = "\n".join(fragmentos)
    elif isinstance(respuesta_cruda, str) and respuesta_cruda.strip().startswith("[{") and "text" in respuesta_cruda:
        try:
            datos_json = json.loads(respuesta_cruda)
            fragmentos = [item.get("text", "") for item in datos_json if isinstance(item, dict) and "text" in item]
            respuesta_texto = "\n".join(fragmentos)
        except:
            respuesta_texto = str(respuesta_cruda)
    else:
        respuesta_texto = str(respuesta_cruda)
        
    print(f"[🤖 {AGENT_NAME}]: {respuesta_texto}")

    return {
        "respuesta_texto": respuesta_texto
    }
