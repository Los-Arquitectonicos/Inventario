"""
Cliente de MongoDB para Lambda
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cliente singleton
_client = None
_db = None


def get_mongodb_client():
    """Obtener cliente de MongoDB (singleton para reutilizar conexión)"""
    global _client, _db
    
    if _client is None:
        mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/pedidos_db')
        
        try:
            _client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Verificar conexión
            _client.admin.command('ping')
            
            # Obtener base de datos
            db_name = mongodb_uri.split('/')[-1] or 'pedidos_db'
            _db = _client[db_name]
            
            logger.info(f"✅ Conectado a MongoDB: {db_name}")
            
        except ConnectionFailure as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    return _db


def get_orders_collection():
    """Obtener colección de pedidos"""
    db = get_mongodb_client()
    return db.orders


def generate_order_number():
    """Generar número de pedido único incremental"""
    collection = get_orders_collection()
    
    # Buscar el último pedido
    last_order = collection.find_one(
        {},
        sort=[("numero_pedido", -1)]
    )
    
    if last_order and last_order.get("numero_pedido"):
        last_num = int(last_order["numero_pedido"].split("-")[1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"PED-{new_num:06d}"


def create_indexes():
    """Crear índices en la colección"""
    collection = get_orders_collection()
    
    # Índice único en numero_pedido
    collection.create_index("numero_pedido", unique=True)
    
    # Índices para queries comunes
    collection.create_index("cliente_id")
    collection.create_index("estado")
    collection.create_index([("fecha_creacion", -1)])
    
    logger.info("✅ Índices creados en MongoDB")
