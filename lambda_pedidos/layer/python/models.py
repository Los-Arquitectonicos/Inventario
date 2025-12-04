"""
Modelos de datos para pedidos en MongoDB
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional


class OrderStatus(str, Enum):
    """Estados del pedido"""
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    EN_PREPARACION = "en_preparacion"
    EN_CAMINO = "en_camino"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class OrderProduct:
    """Producto en el pedido"""
    def __init__(self, producto_id: int, nombre: str, cantidad: int, precio_unitario: float):
        self.producto_id = producto_id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
    
    @property
    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario
    
    def to_dict(self):
        return {
            "producto_id": self.producto_id,
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal
        }


class Order:
    """Pedido completo"""
    def __init__(
        self,
        cliente_id: int,
        productos: List[OrderProduct],
        estado: OrderStatus = OrderStatus.PENDIENTE,
        notas: str = "",
        numero_pedido: Optional[str] = None,
        _id: Optional[str] = None
    ):
        self._id = _id
        self.numero_pedido = numero_pedido
        self.cliente_id = cliente_id
        self.productos = productos
        self.estado = estado
        self.notas = notas
        self.fecha_creacion = datetime.utcnow()
        self.fecha_actualizacion = datetime.utcnow()
        self.historial_estados = [{
            "estado": estado.value,
            "fecha": self.fecha_creacion,
            "comentario": "Pedido creado"
        }]
    
    @property
    def total(self) -> float:
        return sum(p.subtotal for p in self.productos)
    
    def cambiar_estado(self, nuevo_estado: OrderStatus, comentario: str = ""):
        """Cambiar estado del pedido con historial"""
        self.estado = nuevo_estado
        self.fecha_actualizacion = datetime.utcnow()
        self.historial_estados.append({
            "estado": nuevo_estado.value,
            "fecha": self.fecha_actualizacion,
            "comentario": comentario
        })
    
    def to_dict(self):
        """Convertir a diccionario para MongoDB"""
        doc = {
            "numero_pedido": self.numero_pedido,
            "cliente_id": self.cliente_id,
            "productos": [p.to_dict() for p in self.productos],
            "total": self.total,
            "estado": self.estado.value,
            "notas": self.notas,
            "fecha_creacion": self.fecha_creacion,
            "fecha_actualizacion": self.fecha_actualizacion,
            "historial_estados": self.historial_estados
        }
        if self._id:
            doc["_id"] = self._id
        return doc
    
    @classmethod
    def from_dict(cls, data: dict):
        """Crear Order desde documento de MongoDB"""
        productos = [
            OrderProduct(
                producto_id=p["producto_id"],
                nombre=p["nombre"],
                cantidad=p["cantidad"],
                precio_unitario=p["precio_unitario"]
            )
            for p in data.get("productos", [])
        ]
        
        order = cls(
            cliente_id=data["cliente_id"],
            productos=productos,
            estado=OrderStatus(data["estado"]),
            notas=data.get("notas", ""),
            numero_pedido=data.get("numero_pedido"),
            _id=str(data.get("_id"))
        )
        
        order.fecha_creacion = data.get("fecha_creacion", datetime.utcnow())
        order.fecha_actualizacion = data.get("fecha_actualizacion", datetime.utcnow())
        order.historial_estados = data.get("historial_estados", [])
        
        return order
