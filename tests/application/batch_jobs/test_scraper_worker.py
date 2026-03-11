import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# We must import the module we are about to create.
# In TDD, this import might fail initially if the file doesn't exist,
# but we will mock the dependencies first.
try:
    from src.application.batch_jobs.scraper_worker import process_next_job
except ImportError:
    # Dummy placeholder so pytest doesn't completely crash on import error,
    # but the tests will fail because we have no real implementation yet.
    async def process_next_job():
        raise NotImplementedError("worker no implementado")

@pytest.fixture
def dummy_job():
    return {
        "id": 1,
        "category_id": 10,
        "city_id": 20,
        "owner_id": "test_owner",
        "status": "pending",
        "category_name": "Restaurantes",
        "city_name": "Monterrey"
    }

@pytest.mark.asyncio
@patch("src.application.batch_jobs.scraper_worker.StorageService")
@patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
@patch("src.application.batch_jobs.scraper_worker.Bot")
async def test_process_next_job_success(mock_bot_class, mock_scraper_class, mock_storage, dummy_job):
    # Arrange: Configurar Mocks
    mock_storage.get_pending_job.return_value = dummy_job
    
    # Mocking el scraper
    mock_scraper_instance = MagicMock()
    mock_scraper_instance.scrape = AsyncMock(return_value=[{"name": "Lead 1", "phone": "123"}])
    mock_scraper_instance.save_data = MagicMock()
    mock_scraper_class.return_value = mock_scraper_instance
    
    # Mocking StorageService para que retorne archivos simulados
    mock_storage.fetch_excel_files_for_session.return_value = ["/dummy/path/leads.xlsx"]
    mock_storage.obtener_nombre_archivo.side_effect = lambda x: "leads.xlsx"
    mock_storage.obtener_stream_archivo.return_value.__enter__.return_value = b"dummy_content"
    
    # Mocking el Bot de Telegram
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance

    # Act: Ejecutar el worker
    result = await process_next_job()

    # Assert: Verificaciones principales
    assert result is True, "El worker debió retornar True al procesar un trabajo exitosamente"
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'processing')
    mock_scraper_instance.save_data.assert_called_once()
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'completed')
    
    # Assert: Verificaciones de la Unificación (Notificaciones Push)
    # Debe notificar inicio
    mock_bot_instance.send_message.assert_any_call(
        chat_id=dummy_job['owner_id'],
        text=f"🚀 Iniciando extracción asíncrona para {dummy_job['category_name']} en {dummy_job['city_name']}..."
    )
    
    # Debe haber enviado el documento
    mock_storage.fetch_excel_files_for_session.assert_called_once_with(dummy_job['owner_id'])
    mock_bot_instance.send_document.assert_called_once_with(
        chat_id=dummy_job['owner_id'],
        document=b"dummy_content"
    )
    
    # Y finalmente limpiar la sesión para evitar basura
    mock_storage.eliminar_sesion.assert_called_once_with(dummy_job['owner_id'])

@pytest.mark.asyncio
@patch("src.application.batch_jobs.scraper_worker.StorageService")
@patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
async def test_process_next_job_no_pending_jobs(mock_scraper_class, mock_storage):
    # Arrange
    mock_storage.get_pending_job.return_value = None

    # Act
    result = await process_next_job()

    # Assert
    assert result is False, "El worker debió retornar False porque no hay trabajos pendientes"
    mock_storage.update_job_status.assert_not_called()
    mock_scraper_class.assert_not_called()

@pytest.mark.asyncio
@patch("src.application.batch_jobs.scraper_worker.StorageService")
@patch("src.application.batch_jobs.scraper_worker.GoogleMapsScraper")
@patch("src.application.batch_jobs.scraper_worker.Bot")
async def test_process_next_job_handles_exception(mock_bot_class, mock_scraper_class, mock_storage, dummy_job):
    # Arrange
    mock_storage.get_pending_job.return_value = dummy_job
    
    # Simulamos un scraper que explota a mitad del proceso
    mock_scraper_instance = MagicMock()
    mock_scraper_instance.scrape = AsyncMock(side_effect=Exception("Error simulado de red"))
    mock_scraper_class.return_value = mock_scraper_instance
    
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance

    # Act
    result = await process_next_job()

    # Assert
    assert result is False, "El worker debió retornar False porque ocurrió una excepción"
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'processing')
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'failed')
    
    # Debe haber notificado al usuario sobre el error
    mock_bot_instance.send_message.assert_called_with(
        chat_id=dummy_job['owner_id'],
        text=f"❌ Hubo un fallo interno al extraer {dummy_job['category_name']} en {dummy_job['city_name']}. Detalles: Error simulado de red"
    )
