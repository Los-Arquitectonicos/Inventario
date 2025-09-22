from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from ..models import Articulo, Producto, Bodega, MovimientoArticulo

def producto_articulos(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    articulos = Articulo.objects.filter(producto=producto)
    data = []
    for articulo in articulos:
        data.append({
            'id': articulo.pk,
            'codigo_interno': articulo.codigo_interno,
            'numero_serie': articulo.numero_serie,
            'estado': articulo.estado,
            'bodega': articulo.bodega.nombre,
            'fecha_entrada': articulo.fecha_entrada.isoformat(),
        })
    return JsonResponse({'articulos': data})

@csrf_exempt
@require_http_methods(["POST"])
def agregar_articulo(request):
    try:
        data = json.loads(request.body)
        
        producto = Producto.objects.get(id=data['producto_id'])
        bodega = Bodega.objects.get(id=data['bodega_id'])
        
        articulo = Articulo.objects.create(
            producto=producto,
            bodega=bodega,
            numero_serie=data.get('numero_serie'),
            codigo_barras=data.get('codigo_barras'),
            lote=data.get('lote'),
        )
        
        return JsonResponse({
            'success': True,
            'articulo_id': articulo.pk,
            'codigo_interno': articulo.codigo_interno,
            'message': 'Artículo agregado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["PUT"])
def actualizar_articulo_estado(request, articulo_id):
    try:
        data = json.loads(request.body)
        articulo = get_object_or_404(Articulo, id=articulo_id)
        
        estado_anterior = articulo.estado
        articulo.estado = data['estado']
        articulo.save()
        
        MovimientoArticulo.objects.create(
            articulo=articulo,
            tipo_movimiento='cambio_estado',
            estado_anterior=estado_anterior,
            estado_nuevo=articulo.estado,
            motivo=data.get('motivo', 'Cambio de estado via API')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado de {estado_anterior} a {articulo.estado}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)