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
        mock_storage.update_job_status.assert_any_call(101, 'processing')
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
