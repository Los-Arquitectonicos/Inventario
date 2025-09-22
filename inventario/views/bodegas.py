from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Bodega, Articulo

def bodegas_list(request):
    bodegas = Bodega.objects.filter(activa=True)
    data = []
    for bodega in bodegas:
        data.append({
            'id': bodega.pk,
            'nombre': bodega.nombre,
            'codigo': bodega.codigo,
            'ciudad': bodega.ciudad,
            'direccion': bodega.direccion,
        })
    return JsonResponse({'bodegas': data})

def bodega_inventario(request, bodega_id):
    bodega = get_object_or_404(Bodega, id=bodega_id)
    articulos = Articulo.objects.filter(bodega=bodega, estado='disponible')
    
    inventario = {}
    for articulo in articulos:
        sku = articulo.producto.sku
        if sku not in inventario:
            inventario[sku] = {
                'producto_id': articulo.producto.pk,
                'nombre': articulo.producto.nombre,
                'sku': sku,
                'cantidad': 0,
                'articulos': []
            }
        inventario[sku]['cantidad'] += 1
        inventario[sku]['articulos'].append({
            'id': articulo.pk,
            'codigo_interno': articulo.codigo_interno,
            'numero_serie': articulo.numero_serie,
        })
    
    return JsonResponse({
        'bodega': bodega.nombre,
        'inventario': list(inventario.values())
    })