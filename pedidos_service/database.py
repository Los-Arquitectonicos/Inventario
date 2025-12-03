"""
Configuración de conexión a MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """Gestor de conexión a MongoDB"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Conectar a MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
            cls.db = cls.client.get_default_database()
            
            # Verificar conexión
            await cls.client.admin.command('ping')
            logger.info(f"✅ Conectado a MongoDB: {settings.MONGODB_URI}")
            
            # Crear índices
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    @classmethod
    async def create_indexes(cls):
        """Crear índices en la colección de orders"""
        if cls.db is None:
            return
        
        orders_collection = cls.db.orders
        
        # Índice único en numero_pedido
        await orders_collection.create_index("numero_pedido", unique=True)
        
        # Índices para queries comunes
        await orders_collection.create_index("cliente_id")
        await orders_collection.create_index("estado")
        await orders_collection.create_index([("fecha_creacion", -1)])  # Descendente
        
        logger.info("✅ Índices de MongoDB creados")
    
    @classmethod
    async def close(cls):
        """Cerrar conexión a MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("🔌 Conexión a MongoDB cerrada")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Obtener instancia de base de datos"""
        if cls.db is None:
            raise Exception("Database no inicializada. Llamar connect() primero")
        return cls.db


# Helper para obtener la base de datos (Dependency para FastAPI)
def get_database() -> AsyncIOMotorDatabase:
    """Dependency injection para FastAPI"""
    return MongoDB.get_database()
    return MongoDB.get_database()
