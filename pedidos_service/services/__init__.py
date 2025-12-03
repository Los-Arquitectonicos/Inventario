"""
Módulo de servicios
"""
from .inventory_client import InventoryClient
from .order_service import OrderService

__all__ = ["InventoryClient", "OrderService"]
