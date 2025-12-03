"""
Módulo de rutas
"""
from .health import router as health_router
from .orders import router as orders_router

__all__ = ["health_router", "orders_router"]
