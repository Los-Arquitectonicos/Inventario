"""
Lambda: Consultar pedido(s)
GET /pedidos/{numero_pedido} - Obtener un pedido específico
GET /pedidos?cliente_id=X&estado=Y - Listar pedidos con filtros
"""
import json
import logging
from models import Order
from db_client import get_orders_collection
from response_builder import success_response, not_found_response, server_error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Consultar pedido(s)
    
    Paths:
    - GET /pedidos/{numero_pedido} -> Obtener pedido específico
    - GET /pedidos?cliente_id=1&estado=pendiente -> Listar con filtros
    """
    try:
        path_params = event.get('pathParameters', {})
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Caso 1: Obtener pedido específico por número
        if path_params and path_params.get('numero_pedido'):
            return get_pedido_by_numero(path_params['numero_pedido'])
        
        # Caso 2: Listar pedidos con filtros
        return list_pedidos(query_params)
        
    except Exception as e:
        logger.error(f"Error consultando pedidos: {e}", exc_info=True)
        return server_error_response(f"Error al consultar pedidos: {str(e)}")


def get_pedido_by_numero(numero_pedido: str):
    """Obtener un pedido específico"""
    logger.info(f"Consultando pedido {numero_pedido}")
    
    collection = get_orders_collection()
    order_doc = collection.find_one({"numero_pedido": numero_pedido})
    
    if not order_doc:
        return not_found_response(f"Pedido {numero_pedido}")
    
    order = Order.from_dict(order_doc)
    
    return success_response({
        "pedido": order.to_dict()
    })


def list_pedidos(query_params):
    """Listar pedidos con filtros opcionales"""
    logger.info(f"Listando pedidos con filtros: {query_params}")
    
    # Construir query de MongoDB
    query = {}
    
    if query_params.get('cliente_id'):
        query['cliente_id'] = int(query_params['cliente_id'])
    
    if query_params.get('estado'):
        query['estado'] = query_params['estado']
    
    # Paginación
    skip = int(query_params.get('skip', 0))
    limit = int(query_params.get('limit', 100))
    limit = min(limit, 500)  # Máximo 500
    
    collection = get_orders_collection()
    
    # Contar total
    total = collection.count_documents(query)
    
    # Obtener pedidos
    cursor = collection.find(query).sort("fecha_creacion", -1).skip(skip).limit(limit)
    orders = [Order.from_dict(doc).to_dict() for doc in cursor]
    
    logger.info(f"Encontrados {len(orders)} pedidos de {total} totales")
    
    return success_response({
        "total": total,
        "skip": skip,
        "limit": limit,
        "pedidos": orders
    })
