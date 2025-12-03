"""
Schemas Pydantic para request/response del API de pedidos
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from pedidos_service.models.enums import OrderStatus


class ProductInfo(BaseModel):
    """Información de producto desde Django"""
    id: int
    nombre: str
    precio: float = Field(ge=0)
    stock_disponible: int = Field(ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 5,
                "nombre": "Camiseta Azul",
                "precio": 25.00,
                "stock_disponible": 50
            }
        }


class CreateOrderProduct(BaseModel):
    """Producto en request de creación de pedido"""
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 5,
                "cantidad": 3
            }
        }


class CreateOrderRequest(BaseModel):
    """Request para crear un nuevo pedido"""
    cliente_id: int = Field(gt=0)
    productos: List[CreateOrderProduct] = Field(min_length=1)
    notas: Optional[str] = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "cliente_id": 1,
                "productos": [
                    {"producto_id": 5, "cantidad": 3},
                    {"producto_id": 8, "cantidad": 1}
                ],
                "notas": "Entregar antes de las 5pm"
            }
        }


class UpdateOrderStatusRequest(BaseModel):
    """Request para actualizar estado del pedido"""
    nuevo_estado: OrderStatus
    
    class Config:
        json_schema_extra = {
            "example": {
                "nuevo_estado": "preparando"
            }
        }


class OrderProductResponse(BaseModel):
    """Producto en response de pedido"""
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 5,
                "nombre": "Camiseta Azul",
                "cantidad": 3,
                "precio_unitario": 25.00,
                "subtotal": 75.00
            }
        }


class ClienteInfoResponse(BaseModel):
    """Información del cliente en response"""
    nombre: str
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "email": "juan@example.com"
            }
        }


class OrderTimestampsResponse(BaseModel):
    """Timestamps de estados en response"""
    pendiente: Optional[datetime] = None
    preparando: Optional[datetime] = None
    listo: Optional[datetime] = None
    enviado: Optional[datetime] = None
    entregado: Optional[datetime] = None
    cancelado: Optional[datetime] = None


class OrderResponse(BaseModel):
    """Response completa de un pedido"""
    id: str
    numero_pedido: str
    estado: str
    fecha_creacion: datetime
    fecha_completado: Optional[datetime] = None
    cliente_id: int
    cliente_info: Optional[ClienteInfoResponse] = None
    productos: List[OrderProductResponse]
    total: float
    timestamps: OrderTimestampsResponse
    notas: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "numero_pedido": "PED-000001",
                "estado": "pendiente",
                "fecha_creacion": "2024-01-15T10:30:00",
                "fecha_completado": None,
                "cliente_id": 1,
                "cliente_info": {
                    "nombre": "Juan Pérez",
                    "email": "juan@example.com"
                },
                "productos": [
                    {
                        "producto_id": 5,
                        "nombre": "Camiseta Azul",
                        "cantidad": 3,
                        "precio_unitario": 25.00,
                        "subtotal": 75.00
                    }
                ],
                "total": 75.00,
                "timestamps": {
                    "pendiente": "2024-01-15T10:30:00"
                },
                "notas": "Entregar antes de las 5pm"
            }
        }


class OrderListResponse(BaseModel):
    """Response para lista de pedidos"""
    total: int
    pedidos: List[OrderResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "pedidos": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "numero_pedido": "PED-000001",
                        "estado": "pendiente",
                        "fecha_creacion": "2024-01-15T10:30:00",
                        "cliente_id": 1,
                        "productos": [],
                        "total": 75.00
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Response de error"""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Pedido no encontrado"
            }
        }
