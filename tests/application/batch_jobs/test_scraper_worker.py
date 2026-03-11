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
async def test_process_next_job_success(mock_scraper_class, mock_storage, dummy_job):
    # Arrange: Configurar Mocks
    mock_storage.get_pending_job.return_value = dummy_job
    
    # Mocking el scraper
    mock_scraper_instance = MagicMock()
    mock_scraper_instance.scrape = AsyncMock(return_value=[{"name": "Lead 1", "phone": "123"}])
    mock_scraper_instance.save_data = MagicMock()
    mock_scraper_class.return_value = mock_scraper_instance

    # Act: Ejecutar el worker
    result = await process_next_job()

    # Assert: Verificaciones
    assert result is True, "El worker debió retornar True al procesar un trabajo exitosamente"
    
    # 1. Verificamos que se actualizó el estado a 'processing'
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'processing')
    
    # 2. Verificamos que el scraper fue instanciado correctamente
    mock_scraper_class.assert_called_once_with(headless_override=True, session_id=dummy_job['owner_id'])
    
    # 3. Verificamos que se llamó a scrape() con los datos correctos
    mock_scraper_instance.scrape.assert_called_once_with([dummy_job['city_name']], [dummy_job['category_name']])
    mock_scraper_instance.save_data.assert_called_once()
    
    # 4. Verificamos que se actualizó el estado a 'completed' al final
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'completed')

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
async def test_process_next_job_handles_exception(mock_scraper_class, mock_storage, dummy_job):
    # Arrange
    mock_storage.get_pending_job.return_value = dummy_job
    
    # Simulamos un scraper que explota a mitad del proceso
    mock_scraper_instance = MagicMock()
    mock_scraper_instance.scrape = AsyncMock(side_effect=Exception("Error simulado de red"))
    mock_scraper_class.return_value = mock_scraper_instance

    # Act
    result = await process_next_job()

    # Assert
    assert result is False, "El worker debió retornar False porque ocurrió una excepción"
    
    # Debe haber marcado processing primero
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'processing')
    
    # Pero finalmente debe haber marcado failed
    mock_storage.update_job_status.assert_any_call(dummy_job['id'], 'failed')
