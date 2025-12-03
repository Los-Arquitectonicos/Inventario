"""
Lambda: Seguir/actualizar estado de pedido
PUT /pedidos/{numero_pedido}/seguimiento
"""
import json
import logging
from models import Order, OrderStatus
from db_client import get_orders_collection
from response_builder import success_response, not_found_response, validation_error_response, server_error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Transiciones válidas de estado
VALID_TRANSITIONS = {
    OrderStatus.PENDIENTE: [OrderStatus.CONFIRMADO, OrderStatus.CANCELADO],
    OrderStatus.CONFIRMADO: [OrderStatus.EN_PREPARACION, OrderStatus.CANCELADO],
    OrderStatus.EN_PREPARACION: [OrderStatus.EN_CAMINO, OrderStatus.CANCELADO],
    OrderStatus.EN_CAMINO: [OrderStatus.ENTREGADO],
    OrderStatus.ENTREGADO: [],  # Estado final
    OrderStatus.CANCELADO: []   # Estado final
}


def lambda_handler(event, context):
    """
    Actualizar estado de un pedido con seguimiento
    
    Path: PUT /pedidos/{numero_pedido}/seguimiento
    
    Body esperado:
    {
        "nuevo_estado": "confirmado",
        "comentario": "Pedido confirmado por el vendedor"
    }
    """
    try:
        # Obtener número de pedido del path
        path_params = event.get('pathParameters', {})
        numero_pedido = path_params.get('numero_pedido')
        
        if not numero_pedido:
            return validation_error_response("numero_pedido es requerido en el path")
        
        # Parsear body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        nuevo_estado_str = body.get('nuevo_estado')
        comentario = body.get('comentario', '')
        
        if not nuevo_estado_str:
            return validation_error_response("nuevo_estado es requerido")
        
        # Validar que el estado es válido
        try:
            nuevo_estado = OrderStatus(nuevo_estado_str)
        except ValueError:
            estados_validos = [e.value for e in OrderStatus]
            return validation_error_response(
                f"Estado inválido. Estados válidos: {estados_validos}"
            )
        
        logger.info(f"Actualizando pedido {numero_pedido} a estado {nuevo_estado.value}")
        
        # Obtener pedido actual
        collection = get_orders_collection()
        order_doc = collection.find_one({"numero_pedido": numero_pedido})
        
        if not order_doc:
            return not_found_response(f"Pedido {numero_pedido}")
        
        order = Order.from_dict(order_doc)
        estado_actual = order.estado
        
        # Validar transición de estado
        if nuevo_estado not in VALID_TRANSITIONS.get(estado_actual, []):
            return validation_error_response(
                f"Transición inválida de {estado_actual.value} a {nuevo_estado.value}. "
                f"Transiciones permitidas desde {estado_actual.value}: "
                f"{[e.value for e in VALID_TRANSITIONS.get(estado_actual, [])]}"
            )
        
        # Cambiar estado
        order.cambiar_estado(nuevo_estado, comentario)
        
        # Actualizar en MongoDB
        collection.update_one(
            {"numero_pedido": numero_pedido},
            {
                "$set": {
                    "estado": order.estado.value,
                    "fecha_actualizacion": order.fecha_actualizacion,
                    "historial_estados": order.historial_estados
                }
            }
        )
        
        # Obtener pedido actualizado
        updated_doc = collection.find_one({"numero_pedido": numero_pedido})
        updated_order = Order.from_dict(updated_doc)
        
        logger.info(f"✅ Pedido {numero_pedido} actualizado a {nuevo_estado.value}")
        
        return success_response({
            "message": f"Estado actualizado a {nuevo_estado.value}",
            "pedido": updated_order.to_dict()
        })
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return validation_error_response(str(e))
    
    except Exception as e:
        logger.error(f"Error actualizando pedido: {e}", exc_info=True)
        return server_error_response(f"Error al actualizar pedido: {str(e)}")
