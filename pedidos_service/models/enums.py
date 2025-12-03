"""
Enums para el microservicio de Pedidos
"""
from enum import Enum


class OrderStatus(str, Enum):
    """Estados posibles de un pedido"""
    PENDIENTE = "pendiente"      # Pedido creado, esperando procesamiento
    PREPARANDO = "preparando"    # En proceso de alistamiento
    LISTO = "listo"              # Listo para envío
    ENVIADO = "enviado"          # Enviado al cliente
    ENTREGADO = "entregado"      # Entregado y completado
    CANCELADO = "cancelado"      # Cancelado


# Transiciones de estado válidas
STATE_TRANSITIONS = {
    OrderStatus.PENDIENTE: [OrderStatus.PREPARANDO, OrderStatus.CANCELADO],
    OrderStatus.PREPARANDO: [OrderStatus.LISTO, OrderStatus.CANCELADO],
    OrderStatus.LISTO: [OrderStatus.ENVIADO, OrderStatus.CANCELADO],
    OrderStatus.ENVIADO: [OrderStatus.ENTREGADO],
    OrderStatus.ENTREGADO: [],  # Estado final
    OrderStatus.CANCELADO: []   # Estado final
}


def is_valid_transition(current_state: OrderStatus, new_state: OrderStatus) -> bool:
    """Verificar si una transición de estado es válida"""
    return new_state in STATE_TRANSITIONS.get(current_state, [])


def can_cancel(current_state: OrderStatus) -> bool:
    """Verificar si un pedido puede ser cancelado"""
    return current_state in [OrderStatus.PENDIENTE, OrderStatus.PREPARANDO]
