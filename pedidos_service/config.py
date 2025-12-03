"""
Configuración del microservicio de Pedidos
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración del servicio"""
    
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017/orders_db"
    
    # Django InventarioWMS API
    DJANGO_API_URL: str = "http://localhost:8080"
    
    # Service
    SERVICE_PORT: int = 8002
    SERVICE_NAME: str = "pedidos-service"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtener configuración (cached)"""
    return Settings()


settings = get_settings()
