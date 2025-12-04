"""
Lambda: Crear nuevo pedido
POST /pedidos
"""
import json
import logging
from models import Order, OrderProduct, OrderStatus
from db_client import get_orders_collection, generate_order_number
from provesi_client import validate_producto, validate_cliente
from response_builder import success_response, error_response, validation_error_response, server_error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Crear un nuevo pedido
    
    Body esperado:
    {
        "cliente_id": 1,
        "productos": [
            {"producto_id": 5, "cantidad": 3}
        ],
        "notas": "Entregar antes de las 5pm"
    }
    """
    try:
        # Parsear body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        logger.info(f"Creando pedido para cliente {body.get('cliente_id')}")
        
        # Validar campos requeridos
        if not body.get('cliente_id'):
            return validation_error_response("cliente_id es requerido")
        
        if not body.get('productos') or len(body['productos']) == 0:
            return validation_error_response("productos es requerido y debe tener al menos un item")
        
        cliente_id = int(body['cliente_id'])
        notas = body.get('notas', '')
        
        # Validar cliente existe en ProvesiWMS
        cliente_info = validate_cliente(cliente_id)
        if not cliente_info:
            return validation_error_response(f"Cliente {cliente_id} no existe en ProvesiWMS")
        
        # Validar productos y construir lista
        productos = []
        for item in body['productos']:
            producto_id = int(item['producto_id'])
            cantidad = int(item['cantidad'])
            
            if cantidad <= 0:
                return validation_error_response(f"Cantidad debe ser mayor a 0 para producto {producto_id}")
            
            # Validar producto existe
            producto_info = validate_producto(producto_id)
            if not producto_info:
                return validation_error_response(f"Producto {producto_id} no existe en ProvesiWMS")
            
            # Verificar stock
            if producto_info['stock'] < cantidad:
                return validation_error_response(
                    f"Stock insuficiente para {producto_info['nombre']}. "
                    f"Disponible: {producto_info['stock']}, Solicitado: {cantidad}"
                )
            
            productos.append(OrderProduct(
                producto_id=producto_id,
                nombre=producto_info['nombre'],
                cantidad=cantidad,
                precio_unitario=producto_info['precio']
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
