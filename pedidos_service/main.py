"""
Aplicación principal del microservicio de Pedidos
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from pedidos_service.config import settings
from pedidos_service.database import MongoDB
from pedidos_service.routes import health_router, orders_router

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Pedidos Service",
    description="Microservicio de gestión de pedidos para ProvesiWMS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Eventos al iniciar la aplicación"""
    logger.info("🚀 Iniciando Pedidos Service...")
    
    # Conectar a MongoDB
    await MongoDB.connect()
    
    logger.info(f"✅ Pedidos Service corriendo en puerto {settings.SERVICE_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar la aplicación"""
    logger.info("🛑 Cerrando Pedidos Service...")
    
    # Cerrar conexión MongoDB
    await MongoDB.close()
    
    logger.info("👋 Pedidos Service cerrado correctamente")


# Registrar rutas
app.include_router(health_router)
app.include_router(orders_router)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "pedidos-service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
