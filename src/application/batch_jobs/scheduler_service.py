import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from src.infrastructure.database.storage_service import StorageService
from src.application.ai_agents.agent_service import procesar_mensaje_agente

import logging
# El Scheduler usa el logger global configurado por el componente que lo inicia (Bot)
logger = logging.getLogger(__name__)

class SchedulerService:
    _scheduler = AsyncIOScheduler()
    _app: Application = None

    @classmethod
    def iniciar(cls, app: Application):
        """Inicia el scheduler y carga las alertas activas desde la base de datos."""
        logging.getLogger('apscheduler').setLevel(logging.INFO)
        cls._app = app
        cls._scheduler.start()
        logger.info("⏰ [Scheduler] Iniciando motor de alertas programadas...")
        
        # Cargar los jobs persistentes
        alertas = StorageService.obtener_alertas()
        for alerta in alertas:
            cls._programar_job_interno(alerta['id'], alerta['chat_id'], alerta['cron_expression'], alerta['prompt_task'])
        
        logger.info(f"⏰ [Scheduler] {len(alertas)} alertas cargadas exitosamente.")

    @classmethod
    def agendar_alerta(cls, chat_id: str, cron_expression: str, prompt_task: str) -> int:
        """Guarda en BD y agenda en la memoria del ciclo actual."""
        alerta_id = StorageService.guardar_alerta(chat_id, cron_expression, prompt_task)
        cls._programar_job_interno(alerta_id, str(chat_id), cron_expression, prompt_task)
        return alerta_id

    @classmethod
    def eliminar_alerta(cls, alerta_id: int, chat_id: str) -> bool:
        """Elimina de la BD y cancela el job en memoria."""
        exito = StorageService.eliminar_alerta(alerta_id, chat_id)
        if exito:
            job_id = f"alerta_{alerta_id}"
            if cls._scheduler.get_job(job_id):
                cls._scheduler.remove_job(job_id)
        return exito

    @classmethod
    def _programar_job_interno(cls, alerta_id: int, chat_id: str, cron_expression: str, prompt_task: str):
        job_id = f"alerta_{alerta_id}"
        try:
            cls._scheduler.add_job(
                cls._ejecutar_alerta,
                CronTrigger.from_crontab(cron_expression),
                id=job_id,
                args=[chat_id, prompt_task],
                replace_existing=True
            )
            logger.info(f"⏰ [Scheduler] Job {job_id} agendado: '{prompt_task}' con cron: {cron_expression}")
        except Exception as e:
            logger.error(f"❌ [Scheduler] Error validando CRON '{cron_expression}': {str(e)}")

    @classmethod
    async def _ejecutar_alerta(cls, chat_id: str, prompt_task: str):
        """Esta es la función que ejecuta APScheduler a la hora acordada."""
        logger.info(f"⏰ [Scheduler Ejecutando] Tarea programada para chat {chat_id}: {prompt_task}")
        if not cls._app:
            logger.error("❌ [Scheduler] Application de Telegram no referenciada.")
            return

        bot = cls._app.bot
        
        # 1. Avisamos que se disparó la alerta
        mensaje_estado = await bot.send_message(
            chat_id=chat_id, 
            text="⏰ *Alerta Programada:* Procesando tu resumen automático...",
            parse_mode="Markdown"
        )
        
        try:
            # 2. Pasamos el prompt al "Cerebro" (LangGraph)
            resultado = await procesar_mensaje_agente(prompt_task, chat_id)
            
            # 3. Mandamos resultados usando la UI centralizada para cumplir con el principio DRY
            from src.presentation.telegram_bot.telegram_bot import enviar_resultados_al_chat
            await enviar_resultados_al_chat(bot, chat_id, mensaje_estado, resultado)
                
        except Exception as e:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=mensaje_estado.message_id,
                text=f"❌ Error al procesar tu alerta programada: {str(e)}"
            )

