import pytest
import logging
from unittest.mock import MagicMock, patch
from src.domain.engine.scrapers.scraper import GoogleMapsScraper

def test_logger_compatibility():
    """
    Comprueba que el objeto logger del módulo scraper sea del tipo estándar.
    Tras el fix, ya no llamamos a 'end', por lo que no hay crash.
    """
    from src.domain.engine.scrapers.scraper import logger as scraper_logger
    scraper_logger.setLevel(logging.INFO)
    
    # Esta llamada ahora es segura porque no usamos parámetros inválidos
    scraper_logger.info("Test message")

@pytest.mark.asyncio
async def test_progress_logging_output():
    """
    Simula la línea de código del scroll (Loaded X items...) 
    y verifica que se ejecute sin lanzar TypeError (tras el fix).
    """
    from src.domain.engine.scrapers.scraper import logger as scraper_logger
    scraper_logger.setLevel(logging.INFO)
    
    # La línea 215 ahora no tiene el argumento end=
    scraper_logger.info(f"Loaded {10} items...")

@pytest.mark.asyncio
async def test_scraper_search_and_extract_flow_crash_prevention():
    """
    Mockea la página de Playwright y ejecuta la función de búsqueda hasta el bucle de scroll 
    para asegurar que el flujo completo sea estable.
    """
    from unittest.mock import AsyncMock
    from src.domain.engine.scrapers.scraper import logger as scraper_logger
    scraper_logger.setLevel(logging.INFO)

    scraper = GoogleMapsScraper(headless_override=True, db_path=':memory:')
    
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.press = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    
    # Mock behavior to trigger the scroll loop at least once
    async def mock_evaluate(script, *args):
        if "scrollHeight" in script: return 1000
        if "querySelectorAll" in script: return 10
        return None
        
    mock_page.evaluate = AsyncMock(side_effect=mock_evaluate)
    mock_page.query_selector_all = AsyncMock(return_value=[]) # End early after first iteration

    # Esto ya no debe lanzar TypeError
    await scraper.search_and_extract(mock_page, "Test Query")
