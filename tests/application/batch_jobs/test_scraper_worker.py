"""
Suite TDD completa para src/application/batch_jobs/scraper_worker.py

ESTADO ESPERADO: ROJO inicial si falta lógica o dependencias.
VERDE: El worker debe:
1. Obtener un job con status 'pending'.
2. Cambiar status a 'processing'.
3. Ejecutar el scraper.
4. Al terminar, enviar el Excel al chat_id (owner_id) via Telegram Bot.
5. Marcar como 'completed'.

ESTRATEGIA DE MOCKS:
- StorageService: Mockear accesos a DB.
- GoogleMapsScraper: Mockear el scraping real (proceso pesado).
- telegram.Bot: Mockear las notificaciones PUSH.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Mock de dependencias antes de importar el worker para evitar side effects
with patch("src.domain.engine.scrapers.scraper.GoogleMapsScraper", MagicMock()):
    from src.application.batch_jobs.scraper_worker import process_next_job

@pytest.mark.asyncio
class TestScraperWorker:

    @patch("src.application.batch_jobs.scraper_worker.StorageService")
    @patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
    @patch("src.application.batch_jobs.scraper_worker.Bot")
    async def test_proceso_completo_con_notificacion_push(self, mock_bot_class, mock_scraper_class, mock_storage):
        """
        Verifica el flujo 'Happy Path':
        Job encola -> Scraper ejecuta -> Bot envía Excel -> Job completado.
        """
        # 1. Configurar Mocks
        job_mock = {
            'id': 101,
            'owner_id': '555666',
            'city_name': 'Monterrey',
            'category_name': 'Dentistas'
        }
        mock_storage.get_pending_job.return_value = job_mock
        mock_storage.fetch_excel_files_for_session.return_value = ["/tmp/leads_101.xlsx"]
        mock_storage.obtener_nombre_archivo.return_value = "leads_monterrey_dentistas.xlsx"
        
        # Simular stream de archivo
        mock_stream = MagicMock()
        mock_storage.obtener_stream_archivo.return_value.__enter__.return_value = mock_stream

        # Mock del Bot instancia
        mock_bot_inst = MagicMock()
        mock_bot_inst.send_message = AsyncMock()
        mock_bot_inst.send_document = AsyncMock()
        mock_bot_class.return_value = mock_bot_inst

        # Mock del Scraper instancia
        mock_scraper_inst = MagicMock()
        mock_scraper_inst.scrape = AsyncMock()
        mock_scraper_class.return_value = mock_scraper_inst

        # 2. Ejecutar
        result = await process_next_job()

        # 3. Asserts
        assert result is True
        mock_storage.update_job_status.assert_any_call(101, 'completed')
        
        # Verificar que el bot envió el mensaje de inicio y el documento final
        assert mock_bot_inst.send_message.called
        mock_bot_inst.send_document.assert_called_once()
        args, kwargs = mock_bot_inst.send_document.call_args
        assert kwargs['chat_id'] == '555666'
        assert kwargs['document'] == mock_stream

    @patch("src.application.batch_jobs.scraper_worker.StorageService")
    async def test_retorna_false_si_no_hay_jobs_pendientes(self, mock_storage):
        """El worker no debe hacer nada si la cola está vacía."""
        mock_storage.get_pending_job.return_value = None
        
        result = await process_next_job()
        
        assert result is False
        mock_storage.update_job_status.assert_not_called()

    @patch("src.application.batch_jobs.scraper_worker.StorageService")
    @patch("src.application.batch_jobs.scraper_worker.Bot")
    async def test_maneja_error_y_marca_como_failed(self, mock_bot_class, mock_storage):
        """Si el scraper falla, el job debe marcarse como 'failed' y avisar al usuario."""
        mock_storage.get_pending_job.return_value = {'id': 99, 'owner_id': '1', 'city_name': 'X', 'category_name': 'Y'}
        
        with patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper") as mock_scraper_class:
            mock_scraper_inst = mock_scraper_class.return_value
            mock_scraper_inst.scrape.side_effect = Exception("Crash en Playwright")
            
            mock_bot_inst = MagicMock()
            mock_bot_inst.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot_inst

            result = await process_next_job()
            
            assert result is False
            mock_storage.update_job_status.assert_any_call(99, 'failed')
            # Debe informar al usuario por Telegram
            mock_bot_inst.send_message.assert_called()
            # El código real usa "fallo interno"
            assert "fallo" in mock_bot_inst.send_message.call_args[1]['text'].lower()

    @patch("src.application.batch_jobs.scraper_worker.asyncio.sleep")
    @patch("src.application.batch_jobs.scraper_worker.process_next_job")
    async def test_job_delay_usa_variable_de_entorno(self, mock_process, mock_sleep, monkeypatch):
        """Verifica que el Worker respeta la variable JOB_DELAY_SECONDS del entorno en lugar de 2."""
        import asyncio
        from src.application.batch_jobs.scraper_worker import main_loop
        
        # Primera vuelta procesa algo (True), segunda arroja CancelledError para romper el bucle infinito
        mock_process.side_effect = [True, asyncio.CancelledError()]
        monkeypatch.setenv("JOB_DELAY_SECONDS", "45")
        
        with pytest.raises(asyncio.CancelledError):
            await main_loop()
            
        # El código actual de scraper_worker.py arrojará error aquí pues fallará 
        # en inyectar el JOB_DELAY_SECONDS de la env en lugar de '2'.
        mock_sleep.assert_any_call(45)


# =============================================================================
# SPRINT 1 — FASE 1: Worker Dual-Path (Bot free-text vs Frontend FK)
# (Estos tests DEBEN FALLAR en ROJO hasta que se implemente FASE 2)
# =============================================================================

@pytest.mark.asyncio
class TestWorkerDualPath:
    """
    Sprint 1 - FASE 1: El Worker debe manejar dos tipos de jobs:
    - Job de Bot: city_id=None, zona_text="Paris", category_id=None, categoria_text="Dentistas"
    - Job de Frontend: city_id=5, city_name="Monterrey", category_id=3, category_name="Dentistas"

    ESTADO ESPERADO: ROJO — el código actual no tiene zona_text ni categoria_text.
    """

    @patch("src.application.batch_jobs.scraper_worker.StorageService")
    @patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
    @patch("src.application.batch_jobs.scraper_worker.Bot")
    async def test_worker_uses_zona_text_when_city_id_is_none(
        self, mock_bot_class, mock_scraper_class, mock_storage
    ):
        """Test S1-1.5: Worker usa zona_text y categoria_text si city_id/category_id son None (job de Bot)."""
        mock_storage.get_pending_job.return_value = {
            "id": 1,
            "city_id": None,
            "zona_text": "Tokio",
            "category_id": None,
            "categoria_text": "Medicos",
            "owner_id": "owner_1",
        }
        mock_storage.fetch_excel_files_for_session.return_value = []

        mock_bot_inst = MagicMock()
        mock_bot_inst.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot_inst

        mock_scraper_inst = MagicMock()
        mock_scraper_inst.scrape = AsyncMock()
        mock_scraper_class.return_value = mock_scraper_inst

        await process_next_job()

        # El scraper debe recibir las zonas y categorias en texto libre
        mock_scraper_inst.scrape.assert_called_once_with(["Tokio"], ["Medicos"])

    @patch("src.application.batch_jobs.scraper_worker.StorageService")
    @patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
    @patch("src.application.batch_jobs.scraper_worker.Bot")
    async def test_worker_uses_city_and_category_name_when_job_comes_from_frontend(
        self, mock_bot_class, mock_scraper_class, mock_storage
    ):
        """Test S1-1.6: Worker usa city_name y category_name (JOIN) cuando job viene del Frontend."""
        mock_storage.get_pending_job.return_value = {
            "id": 2,
            "city_id": 5,
            "zona_text": None,
            "category_id": 3,
            "categoria_text": None,
            "city_name": "Monterrey",
            "category_name": "Dentistas",
            "owner_id": "owner_1",
        }
        mock_storage.fetch_excel_files_for_session.return_value = []

        mock_bot_inst = MagicMock()
        mock_bot_inst.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot_inst

        mock_scraper_inst = MagicMock()
        mock_scraper_inst.scrape = AsyncMock()
        mock_scraper_class.return_value = mock_scraper_inst

        await process_next_job()

        # El scraper debe recibir los nombres del JOIN, no el ID
        mock_scraper_inst.scrape.assert_called_once_with(["Monterrey"], ["Dentistas"])

@pytest.mark.asyncio
@patch("src.application.batch_jobs.scraper_worker.StorageService")
@patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
@patch("src.application.batch_jobs.scraper_worker.Bot")
async def test_job_continua_si_notificacion_inicio_falla_telegram_forbidden(mock_bot_class, mock_scraper_class, mock_storage):
    """
    ROJO → el worker actualmente ABORTA si la notificación inicial falla con Forbidden.
    El diseño correcto: la notificación es best-effort → el job debe CONTINUAR y completarse.
    """
    import telegram.error
    
    mock_bot_inst = MagicMock()
    # Falla en la notificación de inicio
    mock_bot_inst.send_message = AsyncMock(side_effect=telegram.error.Forbidden("Chat not found"))
    mock_bot_class.return_value = mock_bot_inst

    mock_storage.get_pending_job.return_value = {
        'id': 333, 'owner_id': 'invalid_chat',
        'zona_text': 'Madrid', 'categoria_text': 'Dentistas'
    }
    mock_storage.fetch_excel_files_for_session.return_value = []

    mock_scraper_inst = MagicMock()
    mock_scraper_inst.scrape = AsyncMock()
    mock_scraper_class.return_value = mock_scraper_inst

    result = await process_next_job()

    # La notificación falló, PERO el scraping debe haber ocurrido igual
    mock_scraper_inst.scrape.assert_called_once()
    # El job debe terminar como 'completed' (el scraping fue exitoso)
    mock_storage.update_job_status.assert_called_with(333, 'completed')
    assert result is True


@pytest.mark.asyncio
@patch("src.application.batch_jobs.scraper_worker.StorageService")
@patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
@patch("src.application.batch_jobs.scraper_worker.Bot")
async def test_job_continua_si_notificacion_inicio_falla_telegram_bad_request(mock_bot_class, mock_scraper_class, mock_storage):
    """
    ROJO → 'Chat not found' es BadRequest (no Forbidden). El worker lo deja escapar como excepción
    no capturada, causando el 'Error Crítico' en los logs.
    El diseño correcto: ambos tipos de error de Telegram en la notificación son best-effort.
    """
    import telegram.error

    mock_bot_inst = MagicMock()
    # telegram.error.BadRequest es el error REAL de "Chat not found"
    mock_bot_inst.send_message = AsyncMock(side_effect=telegram.error.BadRequest("Chat not found"))
    mock_bot_class.return_value = mock_bot_inst

    mock_storage.get_pending_job.return_value = {
        'id': 444, 'owner_id': 'tenant_1',
        'zona_text': 'Guadalajara', 'categoria_text': 'Plomeros'
    }
    mock_storage.fetch_excel_files_for_session.return_value = []

    mock_scraper_inst = MagicMock()
    mock_scraper_inst.scrape = AsyncMock()
    mock_scraper_class.return_value = mock_scraper_inst

    result = await process_next_job()

    # El error BadRequest de Telegram NO debe abortar el job
    mock_scraper_inst.scrape.assert_called_once()
    mock_storage.update_job_status.assert_called_with(444, 'completed')
    assert result is True
