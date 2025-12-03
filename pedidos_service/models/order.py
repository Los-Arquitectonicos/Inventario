"""
Modelos de datos para MongoDB
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """ObjectId personalizado para Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class OrderProduct(BaseModel):
    """Producto dentro de un pedido"""
    producto_id: int
    nombre: str
    cantidad: int = Field(gt=0)
    precio_unitario: float = Field(ge=0)
    
    @property
    def subtotal(self) -> float:
        """Calcular subtotal del producto"""
        return self.cantidad * self.precio_unitario
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 5,
                "nombre": "Camiseta Azul",
                "cantidad": 3,
                "precio_unitario": 25.00
            }
        }


class ClienteInfo(BaseModel):
    """Información del cliente (snapshot)"""
    nombre: str
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "email": "juan@example.com"
            }
        }


class OrderTimestamps(BaseModel):
    """Timestamps de cambios de estado"""
    pendiente: Optional[datetime] = None
    preparando: Optional[datetime] = None
    listo: Optional[datetime] = None
    enviado: Optional[datetime] = None
    entregado: Optional[datetime] = None
    cancelado: Optional[datetime] = None


class Order(BaseModel):
    """Modelo de Order en MongoDB"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    numero_pedido: str = Field(..., max_length=100)
    estado: str = "pendiente"
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_completado: Optional[datetime] = None
    cliente_id: int = Field(gt=0)
    cliente_info: Optional[ClienteInfo] = None
    productos: List[OrderProduct] = []
    total: float = Field(default=0, ge=0)
    timestamps: OrderTimestamps = Field(default_factory=OrderTimestamps)
    notas: str = ""
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "numero_pedido": "PED-000001",
                "estado": "pendiente",
                "cliente_id": 1,
                "productos": [
                    {
                        "producto_id": 5,
                        "nombre": "Camiseta Azul",
                        "cantidad": 3,
                        "precio_unitario": 25.00
                    }
                ],
                "notas": "Entregar antes de las 5pm"
            }
        }
