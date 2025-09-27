"""
Vistas para manejar pedidos (Orders) del sistema de inventario.
Incluye operaciones CRUD y funciones especiales para ubicación de productos.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from decimal import Decimal, InvalidOperation
import json
import logging

from ..models import Pedido, DetallePedido, Producto, User

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def listar_pedidos(request):
    """
    Lista todos los pedidos con paginación y filtros opcionales.
    
    Parámetros de consulta:
    - estado: Filtrar por estado del pedido
    - tipo: Filtrar por tipo de pedido
    - cliente: Filtrar por nombre de cliente (búsqueda parcial)
    - usuario_creador: Filtrar por ID del usuario que creó el pedido
    - fecha_desde: Filtrar pedidos desde esta fecha (formato: YYYY-MM-DD)
    - fecha_hasta: Filtrar pedidos hasta esta fecha (formato: YYYY-MM-DD)
    - page: Número de página (default: 1)
    - per_page: Elementos por página (default: 20, max: 100)
    """
    try:
        # Filtros
        queryset = Pedido.objects.select_related('usuario_creador', 'usuario_asignado')
        
        # Filtro por estado
        estado = request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por tipo
        tipo = request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_pedido=tipo)
        
        # Filtro por cliente (búsqueda parcial)
        cliente = request.GET.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente_nombre__icontains=cliente)
        
        # Filtro por usuario creador
        usuario_creador = request.GET.get('usuario_creador')
        if usuario_creador:
            queryset = queryset.filter(usuario_creador_id=usuario_creador)
        
        # Filtros de fecha
        fecha_desde = request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
        
        fecha_hasta = request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
        
        # Paginación
        try:
            page = int(request.GET.get('page', 1))
            per_page = min(int(request.GET.get('per_page', 20)), 100)
        except ValueError:
            page, per_page = 1, 20
        
        start = (page - 1) * per_page
        end = start + per_page
        
        total_count = queryset.count()
        pedidos = queryset[start:end]
        
        # Serializar datos
        pedidos_data = []
        for pedido in pedidos:
            pedidos_data.append({
                'id': pedido.id,
                'numero_pedido': pedido.numero_pedido,
                'tipo_pedido': pedido.tipo_pedido,
                'estado': pedido.estado,
                'fecha_creacion': pedido.fecha_creacion.isoformat(),
                'fecha_requerida': pedido.fecha_requerida.isoformat() if pedido.fecha_requerida else None,
                'fecha_completado': pedido.fecha_completado.isoformat() if pedido.fecha_completado else None,
                'usuario_creador': {
                    'id': pedido.usuario_creador.id,
                    'username': pedido.usuario_creador.username,
                    'nombre_completo': f"{pedido.usuario_creador.first_name} {pedido.usuario_creador.last_name}".strip()
                } if pedido.usuario_creador else None,
                'usuario_asignado': {
                    'id': pedido.usuario_asignado.id,
                    'username': pedido.usuario_asignado.username,
                    'nombre_completo': f"{pedido.usuario_asignado.first_name} {pedido.usuario_asignado.last_name}".strip()
                } if pedido.usuario_asignado else None,
                'cliente_nombre': pedido.cliente_nombre,
                'cliente_email': pedido.cliente_email,
                'cliente_telefono': pedido.cliente_telefono,
                'direccion_entrega': pedido.direccion_entrega,
                'total_articulos': pedido.total_articulos,
                'valor_total': float(pedido.valor_total),
                'notas': pedido.notas,
                'puede_ser_procesado': pedido.puede_ser_procesado()
            })
        
        return JsonResponse({
            'success': True,
            'pedidos': pedidos_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_next': end < total_count,
                'has_previous': page > 1
            },
            'filtros_disponibles': {
                'estados': dict(Pedido.ESTADOS_PEDIDO),
                'tipos': dict(Pedido.TIPOS_PEDIDO)
            }
        })
    
    except Exception as e:
        logger.error(f"Error al listar pedidos: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_pedido(request, pedido_id):
    """
    Obtiene los detalles completos de un pedido específico, incluyendo sus productos y ubicaciones.
    """
    try:
        pedido = Pedido.objects.select_related(
            'usuario_creador', 'usuario_asignado'
        ).prefetch_related(
            'detalles__producto'
        ).get(id=pedido_id)
        
        # Obtener ubicaciones de productos
        ubicaciones = pedido.obtener_ubicaciones_productos()
        
        # Datos del pedido
        pedido_data = {
            'id': pedido.id,
            'numero_pedido': pedido.numero_pedido,
            'tipo_pedido': pedido.tipo_pedido,
            'estado': pedido.estado,
            'fecha_creacion': pedido.fecha_creacion.isoformat(),
            'fecha_requerida': pedido.fecha_requerida.isoformat() if pedido.fecha_requerida else None,
            'fecha_completado': pedido.fecha_completado.isoformat() if pedido.fecha_completado else None,
            'usuario_creador': {
                'id': pedido.usuario_creador.id,
                'username': pedido.usuario_creador.username,
                'nombre_completo': f"{pedido.usuario_creador.first_name} {pedido.usuario_creador.last_name}".strip()
            } if pedido.usuario_creador else None,
            'usuario_asignado': {
                'id': pedido.usuario_asignado.id,
                'username': pedido.usuario_asignado.username,
                'nombre_completo': f"{pedido.usuario_asignado.first_name} {pedido.usuario_asignado.last_name}".strip()
            } if pedido.usuario_asignado else None,
            'cliente_nombre': pedido.cliente_nombre,
            'cliente_email': pedido.cliente_email,
            'cliente_telefono': pedido.cliente_telefono,
            'direccion_entrega': pedido.direccion_entrega,
            'notas': pedido.notas,
            'observaciones_internas': pedido.observaciones_internas,
            'total_articulos': pedido.total_articulos,
            'valor_total': float(pedido.valor_total),
            'puede_ser_procesado': pedido.puede_ser_procesado(),
            'ubicaciones_productos': ubicaciones
        }
        
        return JsonResponse({
            'success': True,
            'pedido': pedido_data
        })
    
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error al obtener pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def crear_pedido(request):
    """
    Crea un nuevo pedido con sus detalles.
    
    Estructura del JSON:
    {
        "numero_pedido": "PED-001" (opcional, se genera automáticamente),
        "tipo_pedido": "venta",
        "estado": "pendiente",
        "fecha_requerida": "2024-01-15T10:00:00Z",
        "usuario_asignado": 1,
        "cliente_nombre": "Juan Pérez",
        "cliente_email": "juan@email.com",
        "cliente_telefono": "+1234567890",
        "direccion_entrega": "Calle 123, Ciudad",
        "notas": "Entregar en horario de oficina",
        "observaciones_internas": "Cliente VIP",
        "detalles": [
            {
                "producto_id": 1,
                "cantidad": 5,
                "precio_unitario": 25.50,
                "notas": "Color azul preferido"
            },
            {
                "producto_id": 2,
                "cantidad": 3,
                "precio_unitario": 15.00
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            # Crear el pedido
            pedido_data = {
                'tipo_pedido': data.get('tipo_pedido', 'venta'),
                'estado': data.get('estado', 'pendiente'),
                'cliente_nombre': data.get('cliente_nombre'),
                'cliente_email': data.get('cliente_email'),
                'cliente_telefono': data.get('cliente_telefono'),
                'direccion_entrega': data.get('direccion_entrega'),
                'notas': data.get('notas'),
                'observaciones_internas': data.get('observaciones_internas'),
            }
            
            # Número de pedido personalizado (opcional)
            if data.get('numero_pedido'):
                pedido_data['numero_pedido'] = data['numero_pedido']
            
            # Fecha requerida
            if data.get('fecha_requerida'):
                pedido_data['fecha_requerida'] = parse_datetime(data['fecha_requerida'])
            
            # Usuario asignado
            if data.get('usuario_asignado'):
                try:
                    pedido_data['usuario_asignado'] = User.objects.get(id=data['usuario_asignado'])
                except User.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Usuario asignado no encontrado'
                    }, status=400)
            
            # Crear el pedido
            pedido = Pedido(**pedido_data)
            pedido.full_clean()  # Validar
            pedido.save()
            
            # Agregar detalles del pedido
            detalles_data = data.get('detalles', [])
            if not detalles_data:
                return JsonResponse({
                    'success': False,
                    'error': 'El pedido debe tener al menos un producto'
                }, status=400)
            
            for detalle_data in detalles_data:
                try:
                    producto = Producto.objects.get(id=detalle_data['producto_id'])
                except Producto.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Producto con ID {detalle_data["producto_id"]} no encontrado'
                    }, status=400)
                
                # Crear detalle
                detalle = DetallePedido(
                    pedido=pedido,
                    producto=producto,
                    cantidad=detalle_data['cantidad'],
                    precio_unitario=Decimal(str(detalle_data.get('precio_unitario', producto.precio_venta))),
                    notas=detalle_data.get('notas')
                )
                detalle.full_clean()
                detalle.save()
            
            # Obtener el pedido completo con ubicaciones
            pedido_completo = Pedido.objects.select_related(
                'usuario_creador', 'usuario_asignado'
            ).prefetch_related('detalles__producto').get(id=pedido.id)
            
            ubicaciones = pedido_completo.obtener_ubicaciones_productos()
            
            return JsonResponse({
                'success': True,
                'message': f'Pedido {pedido.numero_pedido} creado exitosamente',
                'pedido': {
                    'id': pedido.id,
                    'numero_pedido': pedido.numero_pedido,
                    'tipo_pedido': pedido.tipo_pedido,
                    'estado': pedido.estado,
                    'total_articulos': pedido.total_articulos,
                    'valor_total': float(pedido.valor_total),
                    'puede_ser_procesado': pedido.puede_ser_procesado(),
                    'ubicaciones_productos': ubicaciones
                }
            }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos',
            'details': e.message_dict if hasattr(e, 'message_dict') else str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error al crear pedido: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def actualizar_pedido(request, pedido_id):
    """
    Actualiza un pedido existente. Solo permite actualizar ciertos campos según el estado.
    """
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            pedido = Pedido.objects.get(id=pedido_id)
            
            # Campos que siempre se pueden actualizar
            campos_permitidos = [
                'cliente_nombre', 'cliente_email', 'cliente_telefono', 
                'direccion_entrega', 'notas', 'observaciones_internas'
            ]
            
            # Campos adicionales según el estado
            if pedido.estado in ['pendiente', 'preparando']:
                campos_permitidos.extend(['fecha_requerida', 'usuario_asignado', 'tipo_pedido'])
            
            if pedido.estado == 'pendiente':
                campos_permitidos.append('estado')
            
            # Actualizar campos permitidos
            for campo in campos_permitidos:
                if campo in data:
                    if campo == 'fecha_requerida' and data[campo]:
                        setattr(pedido, campo, parse_datetime(data[campo]))
                    elif campo == 'usuario_asignado' and data[campo]:
                        try:
                            setattr(pedido, campo, User.objects.get(id=data[campo]))
                        except User.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Usuario asignado no encontrado'
                            }, status=400)
                    else:
                        setattr(pedido, campo, data[campo])
            
            pedido.full_clean()
            pedido.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Pedido {pedido.numero_pedido} actualizado exitosamente'
            })
    
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos',
            'details': e.message_dict if hasattr(e, 'message_dict') else str(e)
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error al actualizar pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_pedido(request, pedido_id):
    """
    Elimina un pedido. Solo se pueden eliminar pedidos en estado 'pendiente' o 'cancelado'.
    """
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        
        if pedido.estado not in ['pendiente', 'cancelado']:
            return JsonResponse({
                'success': False,
                'error': f'No se puede eliminar un pedido en estado "{pedido.estado}"'
            }, status=400)
        
        numero_pedido = pedido.numero_pedido
        pedido.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Pedido {numero_pedido} eliminado exitosamente'
        })
    
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error al eliminar pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def ubicaciones_productos_pedido(request, pedido_id):
    """
    Endpoint especializado que retorna solo las ubicaciones de productos para un pedido específico.
    Esta es la función principal solicitada: dado un pedido, retorna los productos, 
    cantidades y ubicación en bodega.
    """
    try:
        pedido = Pedido.objects.prefetch_related('detalles__producto').get(id=pedido_id)
        ubicaciones = pedido.obtener_ubicaciones_productos()
        
        return JsonResponse({
            'success': True,
            'pedido_id': pedido.id,
            'numero_pedido': pedido.numero_pedido,
            'estado': pedido.estado,
            'ubicaciones_productos': ubicaciones,
            'resumen': {
                'total_productos': len(ubicaciones),
                'productos_disponibles': sum(1 for u in ubicaciones if u['completamente_disponible']),
                'productos_parciales': sum(1 for u in ubicaciones if not u['completamente_disponible'] and u['cantidad_disponible'] > 0),
                'productos_sin_stock': sum(1 for u in ubicaciones if u['cantidad_disponible'] == 0),
                'puede_ser_procesado': pedido.puede_ser_procesado()
            }
        })
    
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error al obtener ubicaciones del pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cambiar_estado_pedido(request, pedido_id):
    """
    Cambia el estado de un pedido con validaciones de flujo.
    
    JSON esperado:
    {
        "nuevo_estado": "preparando",
        "observaciones": "Iniciando preparación del pedido"
    }
    """
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('nuevo_estado')
        observaciones = data.get('observaciones', '')
        
        if not nuevo_estado:
            return JsonResponse({
                'success': False,
                'error': 'Debe especificar el nuevo estado'
            }, status=400)
        
        # Validar que el estado existe
        estados_validos = [choice[0] for choice in Pedido.ESTADOS_PEDIDO]
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'error': f'Estado inválido. Estados válidos: {", ".join(estados_validos)}'
            }, status=400)
        
        with transaction.atomic():
            pedido = Pedido.objects.get(id=pedido_id)
            estado_anterior = pedido.estado
            
            # Validaciones de flujo de estados
            transiciones_validas = {
                'pendiente': ['preparando', 'cancelado'],
                'preparando': ['listo', 'pendiente', 'cancelado'],
                'listo': ['enviado', 'preparando', 'cancelado'],
                'enviado': ['entregado', 'devuelto'],
                'entregado': ['devuelto'],
                'cancelado': ['pendiente'],  # Solo si no se ha procesado
                'devuelto': ['pendiente']
            }
            
            if nuevo_estado not in transiciones_validas.get(estado_anterior, []):
                return JsonResponse({
                    'success': False,
                    'error': f'No se puede cambiar de "{estado_anterior}" a "{nuevo_estado}"'
                }, status=400)
            
            # Validaciones específicas
            if nuevo_estado == 'preparando' and not pedido.puede_ser_procesado():
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede preparar el pedido: stock insuficiente'
                }, status=400)
            
            # Actualizar estado
            pedido.estado = nuevo_estado
            
            # Actualizar fecha de completado si es necesario
            if nuevo_estado == 'entregado' and not pedido.fecha_completado:
                from django.utils import timezone
                pedido.fecha_completado = timezone.now()
            
            # Agregar observaciones
            if observaciones:
                if pedido.observaciones_internas:
                    pedido.observaciones_internas += f"\n{observaciones}"
                else:
                    pedido.observaciones_internas = observaciones
            
            pedido.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estado del pedido cambiado de "{estado_anterior}" a "{nuevo_estado}"',
                'pedido': {
                    'id': pedido.id,
                    'numero_pedido': pedido.numero_pedido,
                    'estado_anterior': estado_anterior,
                    'estado_actual': nuevo_estado,
                    'fecha_completado': pedido.fecha_completado.isoformat() if pedido.fecha_completado else None
                }
            })
    
    except Pedido.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pedido no encontrado'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error al cambiar estado del pedido {pedido_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }, status=500)