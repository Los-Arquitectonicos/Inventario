"""
Endpoint de health check
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from pedidos_service.database import get_database
from pedidos_service.services import InventoryClient

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Health check endpoint
    
    Verifica:
    - Conexión a MongoDB
    - Conexión a Django InventarioWMS
    """
    # Verificar MongoDB
    try:
        await db.command("ping")
        mongo_status = "ok"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    
    # Verificar Django
    inventory_client = InventoryClient()
    django_ok = await inventory_client.check_health()
    django_status = "ok" if django_ok else "error"
    
    # Determinar status general
    overall_status = "healthy" if mongo_status == "ok" and django_status == "ok" else "unhealthy"
    
    return {
        "status": overall_status,
        "service": "pedidos-service",
        "dependencies": {
            "mongodb": mongo_status,
            "django_inventario": django_status
        }
    }
