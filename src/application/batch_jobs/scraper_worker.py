import asyncio
from typing import Optional
from src.infrastructure.database.storage_service import StorageService
from src.domain.engine.scrapers.scraper import GoogleMapsScraper
from src.core.config import TELEGRAM_BOT_TOKEN
from telegram import Bot

async def process_next_job() -> bool:
    """
    Intenta obtener y procesar el siguiente trabajo pendiente en la cola.
    Retorna True si procesó un trabajo con éxito, False si no había trabajos o si falló.
    """
    # 1. Obtener de la cola
    job = StorageService.get_pending_job()
    if not job:
        return False
    
    job_id = job['id']
    owner_id = job['owner_id']
    city_name = job['city_name']
    category_name = job['category_name']

    # 2. Marcar como procesando
    StorageService.update_job_status(job_id, 'processing')
    print(f"🔄 [Worker] Iniciando Job #{job_id} para {category_name} en {city_name} (Owner: {owner_id})")

    bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

    try:
        if bot:
            await bot.send_message(
                chat_id=owner_id, 
                text=f"🚀 Iniciando extracción asíncrona para {category_name} en {city_name}..."
            )

        # 3. Instanciar el Scraper aislando sesión y en modo headless (para servidor)
        scraper = GoogleMapsScraper(headless_override=True, session_id=owner_id)
        
        # 4. Ejecutar el scraping real
        await scraper.scrape([city_name], [category_name])
        
        # 5. Guardar datos en Excel y actualizar la base de datos de leads maestras
        scraper.save_data()
        
        # 6. Marcar trabajo como completado
        StorageService.update_job_status(job_id, 'completed')
        print(f"✅ [Worker] Job #{job_id} completado con éxito.")
        
        # 7. Enviar archivos resultantes y limpiar sesión
        if bot:
            archivos = StorageService.fetch_excel_files_for_session(owner_id)
            for excel in archivos:
                nombre = StorageService.obtener_nombre_archivo(excel)
                with StorageService.obtener_stream_archivo(excel) as document:
                    await bot.send_document(chat_id=owner_id, document=document)
            StorageService.eliminar_sesion(owner_id)
            
        return True

    except Exception as e:
        # En caso de catástrofe aseguramos que la cola no se bloquee.
        StorageService.update_job_status(job_id, 'failed')
        print(f"❌ [Worker] Error crítico en Job #{job_id}: {str(e)}")
        
        if bot:
            await bot.send_message(
                chat_id=owner_id,
                text=f"❌ Hubo un fallo interno al extraer {category_name} en {city_name}. Detalles: {str(e)}"
            )
            
        return False

async def main_loop(interval_seconds: int = 10):
    """
    Bucle infinito que mantiene vivo al worker consultando la cola.
    """
    print("🚀 [Worker] Scraper Worker Iniciado. Escuchando cola batch_jobs...")
    while True:
        try:
            processed = await process_next_job()
            # Si no procesó nada, duerme más tiempo para no abusar de la DB.
            # Si procesó algo, duerme el intervalo mínimo antes de tomar el siguiente.
            await asyncio.sleep(interval_seconds if not processed else 2)
        except Exception as e:
            print(f"❌ [Worker] Error en el loop principal: {e}")
            await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("🛑 [Worker] Detenido manualmente por el usuario.")
