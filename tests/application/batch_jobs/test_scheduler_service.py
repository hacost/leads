import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Esta importación ya NO debe fallar tras la Fase 2
from src.application.batch_jobs.scheduler_service import SchedulerService

@pytest.mark.asyncio
class TestSchedulerService:
    """
    Suite Completa para SchedulerService (Legacy).
    Verifica la carga de alertas y la ejecución exitosa vía TelegramService.
    """
    
    @patch("src.application.batch_jobs.scheduler_service.StorageService")
    @patch("src.application.batch_jobs.scheduler_service.SchedulerService._scheduler")
    async def test_iniciar_carga_alertas_desde_db(self, mock_scheduler, mock_storage):
        """Verifica que al iniciar el scheduler se consultan las alertas persistentes."""
        mock_scheduler.state = 0 # STATE_STOPPED
        mock_storage.obtener_alertas.return_value = [
            {"id": 1, "chat_id": "123", "cron_expression": "* * * * *", "prompt_task": "Test"}
        ]
        mock_app = MagicMock()
        
        SchedulerService.iniciar(mock_app)
        
        mock_storage.obtener_alertas.assert_called_once()
        mock_scheduler.start.assert_called_once()

    @patch("src.application.batch_jobs.scheduler_service.procesar_mensaje_agente")
    @patch("src.application.batch_jobs.scheduler_service.SchedulerService._scheduler")
    @patch("src.infrastructure.notifications.telegram_service.TelegramService")
    async def test_ejecutar_alerta_exitosa_con_notificador(self, mock_notifier, mock_scheduler, mock_agente):
        """Verifica que la alerta se ejecuta y usa el nuevo notificador profesional."""
        mock_scheduler.state = 0
        mock_agente.return_value = {"respuesta_texto": "Resultado Alerta"}
        
        # Inyectamos una App y Bot falsos
        mock_bot = AsyncMock()
        mock_bot.send_message.return_value = MagicMock(message_id=999)
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        
        SchedulerService.iniciar(mock_app)
        
        # EJECUCIÓN
        await SchedulerService._ejecutar_alerta("8209526798", "Búscame frasess")
        
        # VERIFICACIÓN: Ya NO debe haber error de importación y debe llamar al notificador
        mock_notifier.notificar_resultado_agente.assert_called_once()
        args, kwargs = mock_notifier.notificar_resultado_agente.call_args
        # El resultado es el 4to argumento posicional en _ejecutar_alerta
        assert args[3] == {"respuesta_texto": "Resultado Alerta"}
