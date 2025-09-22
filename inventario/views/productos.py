from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from ..models import Producto, Categoria, Proveedor

def productos_list(request):
    productos = Producto.objects.filter(activo=True)
    data = []
    for producto in productos:
        data.append({
            'id': getattr(producto, 'id', getattr(producto, 'producto_id', None)),
            'nombre': producto.nombre,
            'sku': producto.sku,
            'precio_venta': str(producto.precio_venta),
            'cantidad_total': producto.cantidad_total(),
            'esta_en_stock': producto.esta_en_stock(),
        })
    return JsonResponse({'productos': data})

def producto_detail(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    data = {
        'id': producto.pk,
        'nombre': producto.nombre,
        'sku': producto.sku,
        'descripcion': producto.descripcion,
        'precio_costo': str(producto.precio_costo),
        'precio_venta': str(producto.precio_venta),
        'cantidad_total': producto.cantidad_total(),
        'esta_en_stock': producto.esta_en_stock(),
    }
    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["POST"])
def crear_producto(request):
    try:
        data = json.loads(request.body)
        
        categoria = None
        if data.get('categoria_id'):
            categoria = Categoria.objects.get(id=data['categoria_id'])
            
        proveedor = None
        if data.get('proveedor_id'):
            proveedor = Proveedor.objects.get(id=data['proveedor_id'])
        
        producto = Producto.objects.create(
            nombre=data['nombre'],
            sku=data['sku'],
            descripcion=data.get('descripcion', ''),
            categoria=categoria,
            proveedor=proveedor,
            precio_costo=data['precio_costo'],
            precio_venta=data['precio_venta'],
            stock_minimo=data.get('stock_minimo', 0),
            stock_maximo=data.get('stock_maximo', 1000),
        )
        
        return JsonResponse({
            'success': True,
            'producto_id': producto.pk,
            'message': 'Producto creado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)