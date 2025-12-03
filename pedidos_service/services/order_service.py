"""
Lógica de negocio para gestión de pedidos
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from pedidos_service.models import Order, OrderProduct, ClienteInfo, OrderStatus, is_valid_transition, can_cancel
from pedidos_service.schemas.order import (
    CreateOrderRequest, 
    OrderResponse, 
    OrderProductResponse,
    ClienteInfoResponse,
    OrderTimestampsResponse
)
from pedidos_service.services.inventory_client import InventoryClient

logger = logging.getLogger(__name__)


class OrderService:
    """Servicio de lógica de negocio para pedidos"""
    
    def __init__(self, db: AsyncIOMotorDatabase, inventory_client: InventoryClient):
        self.db = db
        self.orders = db.orders
        self.inventory_client = inventory_client
        
    async def _generate_order_number(self) -> str:
        """Generar número de pedido único incremental"""
        # Obtener el último número de pedido
        last_order = await self.orders.find_one(
            {},
            sort=[("numero_pedido", -1)]
        )
        
        if last_order:
            last_num = int(last_order["numero_pedido"].split("-")[1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"PED-{new_num:06d}"
    
    def _order_to_response(self, order: Dict[str, Any]) -> OrderResponse:
        """Convertir documento de MongoDB a OrderResponse"""
        # Convertir productos
        productos_response = [
            OrderProductResponse(
                producto_id=p["producto_id"],
                nombre=p["nombre"],
                cantidad=p["cantidad"],
                precio_unitario=p["precio_unitario"],
                subtotal=p["cantidad"] * p["precio_unitario"]
            )
            for p in order["productos"]
        ]
        
        # Convertir cliente_info si existe
        cliente_info_response = None
        if order.get("cliente_info"):
            cliente_info_response = ClienteInfoResponse(**order["cliente_info"])
        
        # Convertir timestamps
        timestamps_response = OrderTimestampsResponse(**order.get("timestamps", {}))
        
        return OrderResponse(
            id=str(order["_id"]),
            numero_pedido=order["numero_pedido"],
            estado=order["estado"],
            fecha_creacion=order["fecha_creacion"],
            fecha_completado=order.get("fecha_completado"),
            cliente_id=order["cliente_id"],
            cliente_info=cliente_info_response,
            productos=productos_response,
            total=order["total"],
            timestamps=timestamps_response,
            notas=order.get("notas", "")
        )
    
    async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        """
        Crear un nuevo pedido
        
        1. Validar que productos existen en Django
        2. Obtener info del cliente
        3. Crear documento en MongoDB
        """
        # Validar productos y obtener información
        productos_validados = []
        total = 0.0
        
        for item in request.productos:
            # Consultar producto en Django
            product_info = await self.inventory_client.get_product(item.producto_id)
            
            if not product_info:
                raise ValueError(f"Producto {item.producto_id} no existe")
            
            if product_info.stock_disponible < item.cantidad:
                raise ValueError(
                    f"Stock insuficiente para producto {product_info.nombre}. "
                    f"Disponible: {product_info.stock_disponible}, Solicitado: {item.cantidad}"
                )
            
            # Crear OrderProduct
            order_product = OrderProduct(
                producto_id=item.producto_id,
                nombre=product_info.nombre,
                cantidad=item.cantidad,
                precio_unitario=product_info.precio
            )
            
            productos_validados.append(order_product)
            total += order_product.subtotal
        
        # Obtener información del cliente
        cliente_data = await self.inventory_client.get_cliente(request.cliente_id)
        cliente_info = None
        
        if cliente_data:
            cliente_info = ClienteInfo(
                nombre=cliente_data["nombre"],
                email=cliente_data["email"]
            )
        
        # Generar número de pedido
        numero_pedido = await self._generate_order_number()
        
        # Crear orden
        now = datetime.utcnow()
        order = Order(
            numero_pedido=numero_pedido,
            estado=OrderStatus.PENDIENTE,
            fecha_creacion=now,
            cliente_id=request.cliente_id,
            cliente_info=cliente_info,
            productos=productos_validados,
            total=total,
            notas=request.notas or ""
        )
        
        # Inicializar timestamp pendiente
        order.timestamps.pendiente = now
        
        # Insertar en MongoDB
        order_dict = order.dict(by_alias=True, exclude={"id"})
        result = await self.orders.insert_one(order_dict)
        
        # Obtener documento insertado
        inserted = await self.orders.find_one({"_id": result.inserted_id})
        
        logger.info(f"Pedido {numero_pedido} creado exitosamente")
        
        return self._order_to_response(inserted)
    
    async def get_order(self, numero_pedido: str) -> Optional[OrderResponse]:
        """Obtener un pedido por número"""
        order = await self.orders.find_one({"numero_pedido": numero_pedido})
        
        if not order:
            return None
            
        return self._order_to_response(order)
    
    async def list_orders(
        self, 
        estado: Optional[str] = None,
        cliente_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Listar pedidos con filtros opcionales
        
        Args:
            estado: Filtrar por estado
            cliente_id: Filtrar por cliente
            skip: Offset para paginación
            limit: Límite de resultados
        """
        # Construir filtro
        query = {}
        if estado:
            query["estado"] = estado
        if cliente_id:
            query["cliente_id"] = cliente_id
        
        # Contar total
        total = await self.orders.count_documents(query)
        
        # Obtener pedidos
        cursor = self.orders.find(query).sort("fecha_creacion", -1).skip(skip).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        return {
            "total": total,
            "pedidos": [self._order_to_response(order) for order in orders]
        }
    
    async def update_order_status(self, numero_pedido: str, nuevo_estado: OrderStatus) -> OrderResponse:
        """
        Actualizar estado de un pedido
        
        Valida transiciones de estado según STATE_TRANSITIONS
        """
        # Obtener pedido actual
        order = await self.orders.find_one({"numero_pedido": numero_pedido})
        
        if not order:
            raise ValueError(f"Pedido {numero_pedido} no encontrado")
        
        current_state = OrderStatus(order["estado"])
        
        # Validar transición
        if not is_valid_transition(current_state, nuevo_estado):
            raise ValueError(
                f"Transición inválida de {current_state.value} a {nuevo_estado.value}"
            )
        
        # Actualizar timestamps
        now = datetime.utcnow()
        update_data = {
            "estado": nuevo_estado.value,
            f"timestamps.{nuevo_estado.value}": now
        }
        
        # Si es estado final, agregar fecha_completado
        if nuevo_estado in [OrderStatus.ENTREGADO, OrderStatus.CANCELADO]:
            update_data["fecha_completado"] = now
        
        # Actualizar en DB
        await self.orders.update_one(
            {"numero_pedido": numero_pedido},
            {"$set": update_data}
        )
        
        # Obtener pedido actualizado
        updated_order = await self.orders.find_one({"numero_pedido": numero_pedido})
        
        logger.info(f"Pedido {numero_pedido} actualizado a {nuevo_estado.value}")
        
        return self._order_to_response(updated_order)
    
    async def cancel_order(self, numero_pedido: str) -> OrderResponse:
        """Cancelar un pedido"""
        order = await self.orders.find_one({"numero_pedido": numero_pedido})
        
        if not order:
            raise ValueError(f"Pedido {numero_pedido} no encontrado")
        
        current_state = OrderStatus(order["estado"])
        
        # Validar que se puede cancelar
        if not can_cancel(current_state):
            raise ValueError(
                f"Pedido en estado {current_state.value} no puede ser cancelado"
            )
        
        # Actualizar a cancelado
        return await self.update_order_status(numero_pedido, OrderStatus.CANCELADO)
