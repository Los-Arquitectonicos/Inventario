"""
Módulo de schemas
"""
from .order import (
    CreateOrderRequest,
    CreateOrderProduct,
    UpdateOrderStatusRequest,
    OrderResponse,
    OrderListResponse,
    OrderProductResponse,
    ClienteInfoResponse,
    OrderTimestampsResponse,
    ProductInfo,
    ErrorResponse
)

__all__ = [
    "CreateOrderRequest",
    "CreateOrderProduct",
    "UpdateOrderStatusRequest",
    "OrderResponse",
    "OrderListResponse",
    "OrderProductResponse",
    "ClienteInfoResponse",
    "OrderTimestampsResponse",
    "ProductInfo",
    "ErrorResponse"
]
