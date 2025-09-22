from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import MovimientoArticulo, Articulo

def movimientos_articulo(request, articulo_id):
    articulo = get_object_or_404(Articulo, id=articulo_id)
    movimientos = MovimientoArticulo.objects.filter(articulo=articulo)
    
    data = []
    for movimiento in movimientos:
        data.append({
            'id': getattr(movimiento, 'id', None),
            'tipo_movimiento': movimiento.tipo_movimiento,
            'motivo': movimiento.motivo,
            'fecha': movimiento.fecha.isoformat(),
            'usuario': movimiento.usuario.username if movimiento.usuario else None,
            'estado_anterior': movimiento.estado_anterior,
            'estado_nuevo': movimiento.estado_nuevo,
        })
    
    return JsonResponse({'movimientos': data})