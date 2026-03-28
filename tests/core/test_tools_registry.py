"""
Suite TDD completa para src/core/tools_registry.py

ESTADO ESPERADO: ROJO — las pruebas de Google Maps y Facebook verifican que
se llame a StorageService.create_job(), pero el código actual usa subprocess.run.

Los imports se hacen UNA SOLA VEZ al nivel del módulo para evitar recargar
Playwright+LangGraph (35s) 8 veces.

ESTRATEGIA DE MOCKS (testing_strategy.md):
- subprocess.run: patchear en el módulo `subprocess` globalmente
- StorageService/SchedulerService: patchear en sus módulos fuente ya que
  `tools_registry.py` los importa lazy (dentro de las funciones)
"""
import pytest
from unittest.mock import MagicMock, patch, call

# Import único al nivel del módulo — solo ~35s de carga total
from src.core.tools_registry import (
    ejecutar_scraper_google_maps,
    ejecutar_scraper_facebook,
    gestionar_recordatorio,
)


def _make_config(thread_id: str = "test_user_123") -> dict:
    """Helper que construye el config igual al que LangGraph inyecta a las tools."""
    return {"configurable": {"thread_id": thread_id}}


# =============================================================================
# GRUPO 1: ejecutar_scraper_google_maps → DEBE encolar en batch_jobs
# =============================================================================

class TestToolsEdgeCases:
    """Verifica casos borde y funcionalidades extra de los scrapers."""

    def test_maneja_multiples_zonas_separadas_por_punto_y_coma(self):
        """Si el LLM pasa 'Monterrey; Guadalajara', debe crear un job por cada zona."""
        with patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 99}), \
             patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", return_value=1) as mock_create:

            ejecutar_scraper_google_maps.invoke(
                {"zonas": "Monterrey; Guadalajara", "categorias": "Dentistas"},
                config=_make_config()
            )

            assert mock_create.call_count == 2



# =============================================================================
# GRUPO 3: gestionar_recordatorio — contratos ya existentes
# Los imports son lazy (dentro de la función), se patchea en el módulo fuente
# =============================================================================

class TestGestionarRecordatorio:

    @patch("src.application.batch_jobs.scheduler_service.SchedulerService.agendar_alerta")
    def test_agendar_llama_scheduler_con_parametros_correctos(self, mock_agendar):
        """Agendar debe delegar a SchedulerService.agendar_alerta con owner, cron y prompt."""
        mock_agendar.return_value = 42

        result = gestionar_recordatorio.invoke({
            "accion": "agendar",
            "cron_expression": "0 9 * * 1",
            "prompt_task": "Busca dentistas en Monterrey",
            "alerta_id": 0
        }, config=_make_config("user_123"))

        mock_agendar.assert_called_once_with("user_123", "0 9 * * 1", "Busca dentistas en Monterrey")
        assert "42" in result

    @patch("src.infrastructure.database.storage_service.StorageService.obtener_alertas")
    def test_listar_retorna_alertas_formateadas(self, mock_obtener):
        """Listar debe consultar obtener_alertas y formatear el resultado."""
        mock_obtener.return_value = [
            {"id": 1, "cron_expression": "0 9 * * 1", "prompt_task": "Busca plomeros"},
        ]

        result = gestionar_recordatorio.invoke({
            "accion": "listar",
            "cron_expression": "",
            "prompt_task": "",
            "alerta_id": 0
        }, config=_make_config("user_123"))

        mock_obtener.assert_called_once_with("user_123")
        assert "Busca plomeros" in result

    @patch("src.application.batch_jobs.scheduler_service.SchedulerService.eliminar_alerta")
    def test_borrar_exitoso_con_id_valido(self, mock_eliminar):
        """Borrar con ID válido debe retornar mensaje de éxito."""
        mock_eliminar.return_value = True

        result = gestionar_recordatorio.invoke({
            "accion": "borrar",
            "alerta_id": 5,
            "cron_expression": "",
            "prompt_task": ""
        }, config=_make_config("user_123"))

        mock_eliminar.assert_called_once_with(5, "user_123")
        assert "5" in result and ("xito" in result or "borrad" in result.lower())

    def test_borrar_con_id_cero_retorna_error_sin_llamar_storage(self):
        """Borrar con alerta_id <= 0 debe retornar error inmediatamente."""
        with patch("src.application.batch_jobs.scheduler_service.SchedulerService.eliminar_alerta") as mock_eliminar:
            result = gestionar_recordatorio.invoke({
                "accion": "borrar",
                "alerta_id": 0,
                "cron_expression": "",
                "prompt_task": ""
            }, config=_make_config("user_123"))

            mock_eliminar.assert_not_called()
            assert "error" in result.lower() or "Error" in result


# =============================================================================
# SPRINT 1 — FASE 1: Desacoplamiento Total del Bot de la DB
# (Estos tests DEBEN FALLAR en ROJO hasta que se implemente FASE 2)
# =============================================================================

class TestGoogleMapsHybridLogic:
    """
    PRE Sprint 2.5 - FASE 1: Inteligencia Híbrida del Bot para ambos Catálogos.
    ESTADO ESPERADO: ROJO — el código actual todavía usa get_or_create_category.
    """

    def test_bot_uses_category_id_if_exists_in_master(self):
        """Si la categoría existe en master_categories, el bot usa el category_id estructurado."""
        with patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 99}) as mock_cat, \
             patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_google_maps.invoke({"zonas": "Paris", "categorias": "Restaurantes"}, config=_make_config("user_1"))
            
            mock_cat.assert_called_once_with("Restaurantes")
            kwargs = mock_create.call_args[1]
            assert kwargs["category_id"] == 99
            assert kwargs.get("categoria_text") is None

    def test_bot_uses_category_text_fallback_if_not_found(self):
        """Si la categoría NO existe, usa categoria_text libre y category_id=None."""
        with patch("src.core.tools_registry.StorageService.get_category_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_google_maps.invoke({"zonas": "Paris", "categorias": "Extraterrestres"}, config=_make_config("user_1"))
            
            kwargs = mock_create.call_args[1]
            assert kwargs.get("category_id") is None
            assert kwargs["categoria_text"] == "Extraterrestres"

    def test_bot_uses_city_id_if_exists_in_master(self):
        """Si la ciudad existe en master_cities, el bot usa el city_id y deja zona_text=None."""
        with patch("src.core.tools_registry.StorageService.get_city_by_name", return_value={"id": 5}), \
             patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 99}), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_google_maps.invoke({"zonas": "Monterrey", "categorias": "Dentistas"}, config=_make_config("user_1"))
            
            kwargs = mock_create.call_args[1]
            assert kwargs["city_id"] == 5
            assert kwargs.get("zona_text") is None

    def test_bot_uses_free_text_if_city_not_found(self):
        """Si la ciudad NO existe, se usa zona_text libre y city_id=None."""
        with patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 99}), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_google_maps.invoke({"zonas": "Aldea Perdida", "categorias": "Magos"}, config=_make_config("user_1"))
            
            kwargs = mock_create.call_args[1]
            assert kwargs.get("city_id") is None
            assert kwargs["zona_text"] == "Aldea Perdida"


class TestFacebookHybridLogic:
    """Tests equivalentes para el scraper de Facebook."""

    def test_bot_uses_category_id_if_exists_in_master(self):
        with patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 88}) as mock_cat, \
             patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_facebook.invoke({"zonas": "Madrid", "categorias": "Plomeros"}, config=_make_config("user_2"))
            
            mock_cat.assert_called_once_with("Plomeros")
            kwargs = mock_create.call_args[1]
            assert kwargs["category_id"] == 88
            assert kwargs.get("categoria_text") is None

    def test_bot_uses_category_text_fallback_if_not_found(self):
        with patch("src.core.tools_registry.StorageService.get_category_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_facebook.invoke({"zonas": "Madrid", "categorias": "Unicornios"}, config=_make_config("user_2"))
            
            kwargs = mock_create.call_args[1]
            assert kwargs.get("category_id") is None
            assert kwargs["categoria_text"] == "Unicornios"

    def test_bot_uses_city_id_if_exists_in_master(self):
        with patch("src.core.tools_registry.StorageService.get_city_by_name", return_value={"id": 10}), \
             patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 88}), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_facebook.invoke({"zonas": "Guadalajara", "categorias": "Plomeros"}, config=_make_config("user_2"))
            
            kwargs = mock_create.call_args[1]
            assert kwargs["city_id"] == 10
            assert kwargs.get("zona_text") is None

    def test_bot_uses_free_text_if_city_not_found(self):
        with patch("src.core.tools_registry.StorageService.get_city_by_name", return_value=None), \
             patch("src.core.tools_registry.StorageService.get_category_by_name", return_value={"id": 88}), \
             patch("src.core.tools_registry.StorageService.create_hybrid_job", create=True) as mock_create:
            
            ejecutar_scraper_facebook.invoke({"zonas": "Villa Oculta", "categorias": "Carpinteros"}, config=_make_config("user_2"))
            
            kwargs = mock_create.call_args[1]
            assert kwargs.get("city_id") is None
            assert kwargs["zona_text"] == "Villa Oculta"

