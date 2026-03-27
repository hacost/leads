"""
Suite TDD completa para src/application/ai_agents/agent_service.py

ESTADO ESPERADO: ROJO inicial — los tests verifican el comportamiento objetivo:
- La función retorna SOLO 'respuesta_texto' (sin 'archivos_excel' ni 'se_uso_scraper')
- El código actual retorna las 3 keys → los tests de estructura fallarán
- Los tests de lógica de texto pasarán porque el código de limpieza ya existe

ESTRATEGIA DE MOCKS (testing_strategy.md, capa Application/LangGraph):
- `agente_graph.invoke`: se parchea en el módulo de agent_service donde está importado
- No se llama ningún LLM real ni se ejecuta LangGraph
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage


def _make_ai_message(content: str, tool_calls: list = None) -> AIMessage:
    """Helper que construye un AIMessage simulando la respuesta del LLM."""
    msg = AIMessage(content=content)
    if tool_calls:
        msg.tool_calls = tool_calls
    return msg


def _make_graph_response(messages: list) -> dict:
    """Helper que simula el dict de respuesta de agente_graph.invoke."""
    return {"messages": messages}


# =============================================================================
# GRUPO 1: Estructura del retorno — el diseño objetivo
# =============================================================================

@pytest.mark.asyncio
class TestProcesarMensajeAgente:

    @patch("src.application.ai_agents.agent_service.agente_graph")
    async def test_retorna_dict_solo_con_respuesta_texto(self, mock_graph):
        """
        ROJO: El código actual retorna 3 keys (respuesta_texto, archivos_excel, se_uso_scraper).
        El diseño objetivo es retornar SOLO {'respuesta_texto': str}.
        """
        from src.application.ai_agents.agent_service import procesar_mensaje_agente

        mock_graph.invoke.return_value = _make_graph_response([
            HumanMessage(content="hola"),
            _make_ai_message("Hola, ¿en qué te puedo ayudar?"),
        ])

        result = await procesar_mensaje_agente("hola", thread_id="user_123")

        assert isinstance(result, dict), "Debe retornar un dict"
        assert "respuesta_texto" in result, "Debe tener la key 'respuesta_texto'"
        # En el diseño final NO deben existir estas keys
        assert "archivos_excel" not in result, "No debe retornar 'archivos_excel' (ahora es push del worker)"
        assert "se_uso_scraper" not in result, "No debe retornar 'se_uso_scraper' (flag obsoleto)"

    @patch("src.application.ai_agents.agent_service.agente_graph")
    async def test_limpia_listas_json_en_respuesta_del_llm(self, mock_graph):
        """El código debe extraer 'text' de listas de dicts que retorna Gemini en algunos casos."""
        from src.application.ai_agents.agent_service import procesar_mensaje_agente

        mock_graph.invoke.return_value = _make_graph_response([
            HumanMessage(content="hola"),
            _make_ai_message([{"text": "Hola "}, {"text": "mundo!"}]),
        ])

        result = await procesar_mensaje_agente("hola", thread_id="user_123")

        assert "Hola" in result["respuesta_texto"]
        assert "mundo" in result["respuesta_texto"]

    @patch("src.application.ai_agents.agent_service.agente_graph")
    async def test_propaga_session_id_como_thread_id_en_config(self, mock_graph):
        """El session_id debe pasar al config de LangGraph como thread_id."""
        from src.application.ai_agents.agent_service import procesar_mensaje_agente

        mock_graph.invoke.return_value = _make_graph_response([
            _make_ai_message("respuesta"),
        ])

        await procesar_mensaje_agente("hola", thread_id="sesion_telefono_555")

        # Verificar que invoke fue llamado con el config correcto
        call_kwargs = mock_graph.invoke.call_args
        config_usado = call_kwargs[1].get("config") or call_kwargs[0][1]
        assert config_usado["configurable"]["thread_id"] == "sesion_telefono_555"

    @patch("src.application.ai_agents.agent_service.agente_graph")
    async def test_no_busca_excels_cuando_el_agente_usa_scraper(self, mock_graph):
        """
        ROJO: Con el nuevo diseño, aunque el agente haya callado a ejecutar_scraper,
        NO se debe buscar archivos Excel en disco (el worker ya los enviará por push).
        """
        from src.application.ai_agents.agent_service import procesar_mensaje_agente

        # Simular que el LLM llamó a la herramienta ejecutar_scraper_google_maps
        tool_msg = _make_ai_message("Encolé tu búsqueda", tool_calls=[
            {"name": "ejecutar_scraper_google_maps", "args": {}, "id": "call_1"}
        ])

        mock_graph.invoke.return_value = _make_graph_response([
            HumanMessage(content="Busca dentistas"),
            tool_msg,
            _make_ai_message("Tu búsqueda fue encolada ✅"),
        ])

        with patch("src.infrastructure.database.storage_service.buscar_excels_de_usuario") as mock_buscar:
            result = await procesar_mensaje_agente("Busca dentistas", thread_id="user_456")

            # El diseño objetivo NO debe buscar Excels — el worker los enviará
            mock_buscar.assert_not_called()
            assert "respuesta_texto" in result
