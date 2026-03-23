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

class TestEjecutarScraperGoogleMaps:
    """
    ROJO: El código actual usa subprocess.run. Estos tests verifican que DESPUÉS
    de la refactorización, la tool llame a StorageService.create_job en vez de subprocess.
    """

    def test_encola_job_y_NO_llama_subprocess(self):
        """
        La tool DEBE usar StorageService, NO subprocess.run.
        ROJO: falla porque el código actual sí llama subprocess.
        """
        with patch("subprocess.run") as mock_subprocess, \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_city", return_value=10), \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_category", return_value=20), \
             patch("src.infrastructure.database.storage_service.StorageService.create_job", return_value=99):

            result = ejecutar_scraper_google_maps.invoke(
                {"zonas": "Monterrey", "categorias": "Dentistas"},
                config=_make_config("owner_456")
            )

            # subprocess.run NO debe ser llamado en el nuevo diseño
            mock_subprocess.assert_not_called()
            # El mensaje debe confirmar el encolamiento
            assert "99" in result or "encolad" in result.lower() or "agendad" in result.lower()

    def test_usa_thread_id_como_owner_id(self):
        """El owner_id pasado a create_job debe ser el thread_id del config de LangGraph."""
        with patch("subprocess.run"), \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_city", return_value=1), \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_category", return_value=2), \
             patch("src.infrastructure.database.storage_service.StorageService.create_job", return_value=5) as mock_create:

            ejecutar_scraper_google_maps.invoke(
                {"zonas": "Guadalajara", "categorias": "Plomeros"},
                config=_make_config("chat_id_789")
            )

            # El tercer argumento de create_job debe ser el thread_id
            args = mock_create.call_args[0]
            assert args[2] == "chat_id_789"

    def test_maneja_multiples_zonas_separadas_por_punto_y_coma(self):
        """Si el LLM pasa 'Monterrey; Guadalajara', debe crear un job por cada zona."""
        with patch("subprocess.run"), \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_city", return_value=1), \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_category", return_value=2), \
             patch("src.infrastructure.database.storage_service.StorageService.create_job", return_value=1) as mock_create:

            ejecutar_scraper_google_maps.invoke(
                {"zonas": "Monterrey; Guadalajara", "categorias": "Dentistas"},
                config=_make_config()
            )

            assert mock_create.call_count == 2

    def test_tool_google_maps_fails_on_invalid_city(self):
        """
        Si la ciudad no existe en master_cities, la tool debe informar el error
        y no crear ningún job.
        """
        with patch("src.infrastructure.database.storage_service.StorageService.get_city_by_name", return_value=None), \
             patch("src.infrastructure.database.storage_service.StorageService.create_job") as mock_create:
            
            result = ejecutar_scraper_google_maps.invoke(
                {"zonas": "Ciudad Gótica", "categorias": "Herbolarias"},
                config=_make_config()
            )
            
            mock_create.assert_not_called()
            assert "no son zonas operativas permitidas" in result.lower()


# =============================================================================
# GRUPO 2: ejecutar_scraper_facebook → también debe encolar
# =============================================================================

class TestEjecutarScraperFacebook:

    def test_encola_job_y_NO_llama_subprocess(self):
        """La tool de Facebook también debe encolar en batch_jobs, no usar subprocess."""
        with patch("subprocess.run") as mock_subprocess, \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_city", return_value=5), \
             patch("src.infrastructure.database.storage_service.StorageService.get_or_create_category", return_value=6), \
             patch("src.infrastructure.database.storage_service.StorageService.create_job", return_value=88) as mock_create:

            result = ejecutar_scraper_facebook.invoke(
                {"zonas": "Tijuana", "categorias": "Ferreterías"},
                config=_make_config("user_fb")
            )

            mock_subprocess.assert_not_called()
            mock_create.assert_called_once()
            assert result  # No debe estar vacío


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
