"""
Endpoints para gestión de pedidos
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from pedidos_service.database import get_database
from pedidos_service.services import InventoryClient, OrderService
from pedidos_service.schemas.order import (
    CreateOrderRequest,
    UpdateOrderStatusRequest,
    OrderResponse,
    OrderListResponse,
    ErrorResponse
)
from pedidos_service.models.enums import OrderStatus

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def get_order_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> OrderService:
    """Dependency injection para OrderService"""
    inventory_client = InventoryClient()
    return OrderService(db, inventory_client)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Validación fallida"},
        500: {"model": ErrorResponse, "description": "Error del servidor"}
    }
)
async def create_order(
    request: CreateOrderRequest,
    service: OrderService = Depends(get_order_service)
):
    """
    Crear un nuevo pedido
    
    - Valida que productos existen en Django
    - Verifica stock disponible
    - Crea pedido en estado PENDIENTE
    - Genera número de pedido único
    """
    try:
        order = await service.create_order(request)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear pedido: {str(e)}")


@router.get(
    "",
    response_model=OrderListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Error del servidor"}
    }
)
async def list_orders(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente ID"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    service: OrderService = Depends(get_order_service)
):
    """
    Listar pedidos con filtros opcionales
    
    - Soporta filtrado por estado y cliente
    - Paginación con skip/limit
    - Ordenados por fecha de creación descendente
    """
    try:
        # Validar estado si se proporciona
        if estado:
            try:
                OrderStatus(estado)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estado inválido. Valores permitidos: {[s.value for s in OrderStatus]}"
                )
        
        result = await service.list_orders(
            estado=estado,
            cliente_id=cliente_id,
            skip=skip,
            limit=limit
        )
        
        return OrderListResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar pedidos: {str(e)}")


@router.get(
    "/{numero_pedido}",
    response_model=OrderResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Pedido no encontrado"},
        500: {"model": ErrorResponse, "description": "Error del servidor"}
    }
)
async def get_order(
    numero_pedido: str,
    service: OrderService = Depends(get_order_service)
):
    """
    Obtener un pedido específico por número
    
    - Retorna toda la información del pedido
    - Incluye productos, cliente y timestamps
    """
    try:
        order = await service.get_order(numero_pedido)
        
        if not order:
            raise HTTPException(
                status_code=404,
                detail=f"Pedido {numero_pedido} no encontrado"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener pedido: {str(e)}")


@router.patch(
    "/{numero_pedido}/estado",
    response_model=OrderResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Transición de estado inválida"},
        404: {"model": ErrorResponse, "description": "Pedido no encontrado"},
        500: {"model": ErrorResponse, "description": "Error del servidor"}
    }
)
async def update_order_status(
    numero_pedido: str,
    request: UpdateOrderStatusRequest,
    service: OrderService = Depends(get_order_service)
):
    """
    Actualizar estado de un pedido
    
    - Valida transiciones de estado según máquina de estados
    - Actualiza timestamps correspondientes
    - Marca fecha_completado para estados finales
    
    Transiciones válidas:
    - PENDIENTE → PREPARANDO, CANCELADO
    - PREPARANDO → LISTO, CANCELADO
    - LISTO → ENVIADO, CANCELADO
    - ENVIADO → ENTREGADO
    - ENTREGADO, CANCELADO → (estados finales, sin transiciones)
    """
    try:
        order = await service.update_order_status(numero_pedido, request.nuevo_estado)
        return order
        
    except ValueError as e:
        # Puede ser "pedido no encontrado" o "transición inválida"
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado: {str(e)}")


@router.post(
    "/{numero_pedido}/cancelar",
    response_model=OrderResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Pedido no puede ser cancelado"},
        404: {"model": ErrorResponse, "description": "Pedido no encontrado"},
        500: {"model": ErrorResponse, "description": "Error del servidor"}
    }
)
async def cancel_order(
    numero_pedido: str,
    service: OrderService = Depends(get_order_service)
):
    """
    Cancelar un pedido
    
    - Solo se pueden cancelar pedidos en estado PENDIENTE o PREPARANDO
    - Actualiza estado a CANCELADO y marca fecha_completado
    """
    try:
        order = await service.cancel_order(numero_pedido)
        return order
        
    except ValueError as e:
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar pedido: {str(e)}")
