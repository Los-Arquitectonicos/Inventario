"""
Handler unificado para Lambda Function URL
Maneja todas las rutas de pedidos desde una única función Lambda
"""
import json
import logging
import re
from typing import Dict, Any

# Importar handlers de cada función
import sys
import os

# Agregar layer al path
sys.path.insert(0, '/opt/python')

from models import Order, OrderProduct, OrderStatus
from db_client import get_orders_collection, generate_order_number
# provesi_client importación comentada - ya no se usa validación externa
# from provesi_client import validate_producto, validate_cliente
from response_builder import success_response, error_response, validation_error_response, server_error_response, not_found_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Handler principal para Function URL
    
    Function URL event format:
    {
        "requestContext": {
            "http": {
                "method": "GET|POST|PUT|DELETE",
                "path": "/pedidos/PED-000001"
            }
        },
        "rawPath": "/pedidos/PED-000001",
        "rawQueryString": "cliente_id=1&estado=pendiente",
        "body": "...",
        "isBase64Encoded": false
    }
    """
    try:
        # Extraer método y path
        http_method = event['requestContext']['http']['method']
        path = event.get('rawPath', '/')
        
        logger.info(f"📨 {http_method} {path}")
        
        # Parsear query string
        query_params = {}
        if event.get('rawQueryString'):
            for param in event['rawQueryString'].split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        
        # Parsear body si existe
        body = None
        if event.get('body'):
            if event.get('isBase64Encoded'):
                import base64
                body = json.loads(base64.b64decode(event['body']))
            else:
                body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        # Router: despachar según método y path
        return route_request(http_method, path, query_params, body)
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}")
        return error_response("Body debe ser JSON válido", 400)
    
    except Exception as e:
        logger.error(f"Error en handler: {e}", exc_info=True)
        return server_error_response(f"Error interno: {str(e)}")


def route_request(method: str, path: str, query_params: Dict, body: Any):
    """Router de peticiones según método y path"""
    
    # POST /pedidos - Crear pedido
    if method == 'POST' and path == '/pedidos':
        return crear_pedido(body)
    
    # GET /pedidos - Listar pedidos
    if method == 'GET' and path == '/pedidos':
        return listar_pedidos(query_params)
    
    # GET /pedidos/{numero_pedido} - Obtener pedido específico
    match = re.match(r'^/pedidos/([A-Z]+-\d+)$', path)
    if method == 'GET' and match:
        numero_pedido = match.group(1)
        return obtener_pedido(numero_pedido)
    
    # PUT /pedidos/{numero_pedido}/seguimiento - Actualizar seguimiento
    match = re.match(r'^/pedidos/([A-Z]+-\d+)/seguimiento$', path)
    if method == 'PUT' and match:
        numero_pedido = match.group(1)
        return actualizar_seguimiento(numero_pedido, body)
    
    # Ruta no encontrada
    return error_response(f"Ruta no encontrada: {method} {path}", 404)


# ====================================================================================
# HANDLERS DE CADA OPERACIÓN
# ====================================================================================

def crear_pedido(body: Dict) -> Dict:
    """
    POST /pedidos
    Crear un nuevo pedido
    """
    try:
        if not body:
            return validation_error_response("Body es requerido")
        
        logger.info(f"Creando pedido para cliente {body.get('cliente_id')}")
        
        # Validar campos requeridos
        if not body.get('cliente_id'):
            return validation_error_response("cliente_id es requerido")
        
        if not body.get('productos') or len(body['productos']) == 0:
            return validation_error_response("productos es requerido y debe tener al menos un item")
        
        cliente_id = int(body['cliente_id'])
        notas = body.get('notas', '')
        
        # NOTA: NO se valida con ProvesiWMS para evitar dependencias
        # El servicio de pedidos confía en los datos recibidos
        
        # Validar productos y construir lista
        productos = []
        for item in body['productos']:
            producto_id = int(item['producto_id'])
            cantidad = int(item['cantidad'])
            
            if cantidad <= 0:
                return validation_error_response(f"Cantidad debe ser mayor a 0 para producto {producto_id}")
            
            # Obtener datos opcionales del producto desde el request
            nombre_producto = item.get('nombre', f'Producto {producto_id}')
            precio_unitario = float(item.get('precio', 0.0))
            
            productos.append(OrderProduct(
                producto_id=producto_id,
                nombre=nombre_producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            ))
        
        # Generar número de pedido
        numero_pedido = generate_order_number()
        
        # Crear pedido
        order = Order(
            cliente_id=cliente_id,
            productos=productos,
            estado=OrderStatus.PENDIENTE,
            notas=notas,
            numero_pedido=numero_pedido
        )
        
        # Guardar en MongoDB
        collection = get_orders_collection()
        result = collection.insert_one(order.to_dict())
        
        # Obtener documento insertado
        inserted_order = collection.find_one({"_id": result.inserted_id})
        order_dict = Order.from_dict(inserted_order).to_dict()
        
        logger.info(f"✅ Pedido {numero_pedido} creado exitosamente")
        
        return success_response({
            "message": "Pedido creado exitosamente",
            "pedido": order_dict
        }, 201)
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return validation_error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error creando pedido: {e}", exc_info=True)
        return server_error_response(f"Error al crear pedido: {str(e)}")


def listar_pedidos(query_params: Dict) -> Dict:
    """
    GET /pedidos?cliente_id=1&estado=pendiente
    Listar pedidos con filtros opcionales
    """
    try:
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
        
        pedidos = []
        for doc in cursor:
            order = Order.from_dict(doc)
            pedidos.append(order.to_dict())
        
        return success_response({
            "pedidos": pedidos,
            "total": total,
            "skip": skip,
            "limit": limit
        })
        
    except Exception as e:
        logger.error(f"Error listando pedidos: {e}", exc_info=True)
        return server_error_response(f"Error al listar pedidos: {str(e)}")


def obtener_pedido(numero_pedido: str) -> Dict:
    """
    GET /pedidos/{numero_pedido}
    Obtener un pedido específico
    """
    try:
        logger.info(f"Consultando pedido {numero_pedido}")
        
        collection = get_orders_collection()
        order_doc = collection.find_one({"numero_pedido": numero_pedido})
        
        if not order_doc:
            return not_found_response(f"Pedido {numero_pedido}")
        
        order = Order.from_dict(order_doc)
        
        return success_response({
            "pedido": order.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo pedido: {e}", exc_info=True)
        return server_error_response(f"Error al obtener pedido: {str(e)}")


def actualizar_seguimiento(numero_pedido: str, body: Dict) -> Dict:
    """
    PUT /pedidos/{numero_pedido}/seguimiento
    Actualizar seguimiento de pedido
    """
    try:
        if not body:
            return validation_error_response("Body es requerido")
        
        logger.info(f"Actualizando seguimiento de pedido {numero_pedido}")
        
        # Validar campos
        nuevo_estado = body.get('nuevo_estado')
        comentario = body.get('comentario', '')
        
        if not nuevo_estado:
            return validation_error_response("nuevo_estado es requerido")
        
        # Validar estado válido
        try:
            estado_enum = OrderStatus(nuevo_estado)
        except ValueError:
            estados_validos = [e.value for e in OrderStatus]
            return validation_error_response(
                f"Estado '{nuevo_estado}' no válido. Estados válidos: {', '.join(estados_validos)}"
            )
        
        # Obtener pedido actual
        collection = get_orders_collection()
        order_doc = collection.find_one({"numero_pedido": numero_pedido})
        
        if not order_doc:
            return not_found_response(f"Pedido {numero_pedido}")
        
        order = Order.from_dict(order_doc)
        
        # Validar transición de estado
        VALID_TRANSITIONS = {
            OrderStatus.PENDIENTE: [OrderStatus.CONFIRMADO, OrderStatus.CANCELADO],
            OrderStatus.CONFIRMADO: [OrderStatus.EN_PREPARACION, OrderStatus.CANCELADO],
            OrderStatus.EN_PREPARACION: [OrderStatus.EN_CAMINO, OrderStatus.CANCELADO],
            OrderStatus.EN_CAMINO: [OrderStatus.ENTREGADO],
            OrderStatus.ENTREGADO: [],
            OrderStatus.CANCELADO: []
        }
        
        if estado_enum not in VALID_TRANSITIONS.get(order.estado, []):
            return validation_error_response(
                f"No se puede cambiar de '{order.estado.value}' a '{nuevo_estado}'. "
                f"Transiciones válidas: {[e.value for e in VALID_TRANSITIONS.get(order.estado, [])]}"
            )
        
        # Actualizar seguimiento
        from datetime import datetime
        seguimiento_entry = {
            "estado": nuevo_estado,
            "comentario": comentario,
            "fecha": datetime.utcnow()
        }
        
        # Actualizar en MongoDB
        result = collection.update_one(
            {"numero_pedido": numero_pedido},
            {
                "$set": {
                    "estado": nuevo_estado,
                    "fecha_actualizacion": datetime.utcnow()
                },
                "$push": {
                    "seguimiento": seguimiento_entry
                }
            }
        )
        
        if result.modified_count == 0:
            return server_error_response("No se pudo actualizar el pedido")
        
        # Obtener pedido actualizado
        updated_doc = collection.find_one({"numero_pedido": numero_pedido})
        updated_order = Order.from_dict(updated_doc)
        
        logger.info(f"✅ Seguimiento actualizado: {numero_pedido} -> {nuevo_estado}")
        
        return success_response({
            "message": "Seguimiento actualizado exitosamente",
            "pedido": updated_order.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error actualizando seguimiento: {e}", exc_info=True)
        return server_error_response(f"Error al actualizar seguimiento: {str(e)}")
