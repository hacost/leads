import logging
from fastapi import FastAPI
from src.core.logging_config import setup_logging

# Setup senior logging for API
setup_logging("API")

# Forzar formato en loggers de uvicorn que suelen ignorar el root logger
for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    uv_logger = logging.getLogger(logger_name)
    for handler in uv_logger.handlers:
        from src.core.logging_config import ComponentFormatter
        handler.setFormatter(ComponentFormatter("API"))
from fastapi.middleware.cors import CORSMiddleware
from src.presentation.api.auth import router as auth_router
from src.presentation.api.master_cities import router as master_cities_router
from src.presentation.api.categories import router as categories_router
from src.presentation.api.jobs import router as jobs_router
from src.presentation.api.admin import router as admin_router
from src.presentation.api.leads import router as leads_router

app = FastAPI(
    title="Bastion Core API",
    description="API for managing Batch Scraper Jobs and tenant resources",
    version="1.0.0"
)

# Configure CORS to allow Next.js Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
