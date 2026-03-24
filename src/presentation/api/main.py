import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.logging_config import setup_logging
from src.core.config import ALLOWED_ORIGINS

# Router imports
from .auth import router as auth_router
from .master_cities import router as master_cities_router
from .categories import router as categories_router
from .jobs import router as jobs_router
from .admin import router as admin_router
from .leads import router as leads_router

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

def init_app_logging():
    # Setup senior logging for API
    setup_logging("API")
    # Forzar formato en loggers de uvicorn que suelen ignorar el root logger
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uv_logger = logging.getLogger(logger_name)
        for handler in uv_logger.handlers:
            from src.core.logging_config import ComponentFormatter
            handler.setFormatter(ComponentFormatter("API"))

# Solo inicializar logging si no estamos en modo test (detectado por la presencia de pytest o ejecución directa)
if "pytest" not in sys.modules and __name__ == "__main__":
    init_app_logging()

app = FastAPI(
    title="Bastion Core API",
    description="API for managing Batch Scraper Jobs and tenant resources",
    version="1.0.0"
)

@app.exception_handler(HTTPException)
async def professional_http_exception_handler(request: Request, exc: HTTPException):
    """
    Manejador global para profesionalizar las respuestas de error, 
    especialmente las de autorización (403).
    """
    if exc.status_code == 403:
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": str(exc.detail),
                "code": "AUTH_ERROR"
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Configure CORS to allow Next.js Frontend access (Dynamic from Config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(master_cities_router)
app.include_router(categories_router)
app.include_router(jobs_router)
app.include_router(admin_router)
app.include_router(leads_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Bastion Core API is running"}
