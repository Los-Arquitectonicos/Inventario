from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, F
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    Bodega, UbicacionBodega, Producto, Articulo, Cliente, Usuario,
    Cotizacion, Pedido, PedidoProducto, PedidoArticulo, Factura
)
from .auth_utils import (
    require_permission, require_roles, jwt_required, 
    api_require_permission, log_access_attempt
)

# =========================
# VISTAS PRINCIPALES
# =========================

def index(request):
    """
    Vista principal del dashboard de inventario.
    Muestra estadísticas generales y resumen del sistema.
    """
    context = {
        'total_productos': Producto.objects.count(),
        'total_bodegas': Bodega.objects.count(),
        'total_clientes': Cliente.objects.count(),
        'pedidos_pendientes': Pedido.objects.filter(estado='pendiente').count(),
        'productos_sin_stock': Producto.objects.filter(cantidad_stock=0).count(),
    }
    return render(request, 'inventario/index.html', context)

# =========================
# VISTAS DE PRODUCTOS
# =========================

class ProductoListView(ListView):
    """
    Vista para listar todos los productos con funcionalidad de búsqueda.
    Permite filtrar por nombre, marca o descripción.
    """
    model = Producto
    template_name = 'inventario/productos/lista.html'
    context_object_name = 'productos'
    paginate_by = 20

    def get_queryset(self):
        queryset = Producto.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(marca__icontains=search) |
                Q(descripcion__icontains=search)
            )
        return queryset.order_by('nombre')

class ProductoDetailView(DetailView):
    """
    Vista detallada de un producto específico.
    Muestra información completa y artículos relacionados.
    """
    model = Producto
    template_name = 'inventario/productos/detalle.html'
    context_object_name = 'producto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articulos'] = self.object.articulo_set.all() # type: ignore
        context['margen_ganancia'] = self.object.calcular_margen_ganancia() # type: ignore
        return context

def productos_sin_stock(request):
    """
    Vista que muestra productos sin stock disponible.
    Útil para gestión de inventario y reabastecimiento.
    """
    productos = Producto.objects.filter(cantidad_stock=0)
    return render(request, 'inventario/productos/sin_stock.html', {
        'productos': productos
    })

@csrf_exempt
@jwt_required
@require_permission('can_manage_inventory')
def crear_producto(request):
    """
    Vista para crear un nuevo producto mediante POST request.
    Acepta datos JSON y crea un producto en el sistema.
    """
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Extract product data
            nombre = data.get('nombre')
            descripcion = data.get('descripcion', '')
            marca = data.get('marca', '')
            precio_costo = Decimal(str(data.get('precio_costo', 0)))
            precio_venta = Decimal(str(data.get('precio_venta', 0)))
            cantidad_stock = int(data.get('cantidad_stock', 0))
            sku = data.get('sku', '')
            categoria = data.get('categoria', '')
            
            # Validar campos requeridos
            if not nombre:
                return JsonResponse({
                    'error': 'El nombre del producto es requerido'
                }, status=400)
            
            if precio_costo <= 0 or precio_venta <= 0:
                return JsonResponse({
                    'error': 'Los precios deben ser mayores a cero'
                }, status=400)
            
            # Verificar que el SKU no exista
            if sku and Producto.objects.filter(sku=sku).exists():
                return JsonResponse({
                    'error': f'Ya existe un producto con SKU: {sku}'
                }, status=400)
            
            # Obtener campos adicionales según el modelo
            peso = Decimal(str(data.get('peso', 0)))
            dimensiones = data.get('dimensiones', '')
            color = data.get('color', '')
            talla = data.get('talla', '')
            
            # Crear el producto
            producto = Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                marca=marca,
                precio_costo=precio_costo,
                precio_venta=precio_venta,
                cantidad_stock=cantidad_stock,
                peso=peso,
                dimensiones=dimensiones,
                color=color,
                talla=talla
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Producto creado exitosamente',
                'producto': {
                    'id': producto.pk,
                    'nombre': producto.nombre,
                    'marca': producto.marca,
                    'precio_venta': float(producto.precio_venta),
                    'cantidad_stock': producto.cantidad_stock,
                    'color': producto.color,
                    'talla': producto.talla,
                    'margen_ganancia': float(producto.calcular_margen_ganancia())
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Formato JSON inválido'
            }, status=400)
        except ValueError as e:
            return JsonResponse({
                'error': f'Datos inválidos: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': f'Error interno: {str(e)}'
            }, status=500)
    
    else:
        # GET request - mostrar formulario
        return render(request, 'inventario/productos/crear.html')

@jwt_required
@require_permission('can_manage_inventory')
def actualizar_producto(request, producto_id):
    """
    Vista para actualizar un producto existente.
    """
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Actualizar campos
            producto.nombre = data.get('nombre', producto.nombre)
            producto.descripcion = data.get('descripcion', producto.descripcion)
            producto.marca = data.get('marca', producto.marca)
            
            if 'precio_costo' in data:
                producto.precio_costo = Decimal(str(data['precio_costo']))
            if 'precio_venta' in data:
                producto.precio_venta = Decimal(str(data['precio_venta']))
            if 'cantidad_stock' in data:
                producto.cantidad_stock = int(data['cantidad_stock'])
            if 'peso' in data:
                producto.peso = Decimal(str(data['peso']))
            
            producto.dimensiones = data.get('dimensiones', producto.dimensiones)
            producto.color = data.get('color', producto.color)
            producto.talla = data.get('talla', producto.talla)
            
            producto.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Producto actualizado exitosamente',
                'producto': {
                    'id': producto.pk,
                    'nombre': producto.nombre,
                    'marca': producto.marca,
                    'precio_venta': float(producto.precio_venta),
                    'cantidad_stock': producto.cantidad_stock,
                    'color': producto.color,
                    'talla': producto.talla
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'GET':
        return render(request, 'inventario/productos/editar.html', {'producto': producto})

@jwt_required
@require_permission('can_manage_inventory')
def eliminar_producto(request, producto_id):
    """
    Vista para eliminar un producto.
    """
    if request.method == 'DELETE':
        try:
            producto = get_object_or_404(Producto, id=producto_id)
            nombre = producto.nombre
            producto.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Producto "{nombre}" eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# =========================
# VISTAS DE BODEGAS
# =========================

class BodegaListView(ListView):
    """
    Vista para listar todas las bodegas del sistema.
    """
    model = Bodega
    template_name = 'inventario/bodegas/lista.html'
    context_object_name = 'bodegas'

class BodegaDetailView(DetailView):
    """
    Vista detallada de una bodega específica.
    Muestra ubicaciones y capacidad total.
    """
    model = Bodega
    template_name = 'inventario/bodegas/detalle.html'
    context_object_name = 'bodega'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ubicaciones'] = self.object.ubicacionbodega_set.all() # type: ignore
        context['capacidad_total'] = self.object.obtener_capacidad_total() # type: ignore
        return context

@csrf_exempt
def crear_bodega(request):
    """
    Vista para crear una nueva bodega.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            nombre = data.get('nombre')
            ciudad = data.get('ciudad', '')
            direccion = data.get('direccion', '')
            
            if not nombre:
                return JsonResponse({
                    'error': 'El nombre de la bodega es requerido'
                }, status=400)
            
            bodega = Bodega.objects.create(
                nombre=nombre,
                ciudad=ciudad,
                direccion=direccion
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Bodega creada exitosamente',
                'bodega': {
                    'id': bodega.pk,
                    'nombre': bodega.nombre,
                    'ciudad': bodega.ciudad,
                    'direccion': bodega.direccion
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return render(request, 'inventario/bodegas/crear.html')

def actualizar_bodega(request, bodega_id):
    """
    Vista para actualizar una bodega existente.
    """
    bodega = get_object_or_404(Bodega, id=bodega_id)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            bodega.nombre = data.get('nombre', bodega.nombre)
            bodega.ciudad = data.get('ciudad', bodega.ciudad)
            bodega.direccion = data.get('direccion', bodega.direccion)
            
            bodega.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Bodega actualizada exitosamente',
                'bodega': {
                    'id': bodega.pk,
                    'nombre': bodega.nombre,
                    'ciudad': bodega.ciudad,
                    'direccion': bodega.direccion
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    elif request.method == 'GET':
        return render(request, 'inventario/bodegas/editar.html', {'bodega': bodega})

def eliminar_bodega(request, bodega_id):
    """
    Vista para eliminar una bodega.
    """
    if request.method == 'DELETE':
        try:
            bodega = get_object_or_404(Bodega, id=bodega_id)
            nombre = bodega.nombre
            bodega.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Bodega "{nombre}" eliminada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# =========================
# CRUD UBICACIONES DE BODEGA
# =========================

@csrf_exempt
def crear_ubicacion_bodega(request):
    """
    Vista para crear una nueva ubicación de bodega.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            bodega_id = data.get('bodega_id')
            pasillo = data.get('pasillo')
            estante = data.get('estante')
            nivel = data.get('nivel')
            capacidad_total = int(data.get('capacidad_total', 0))
            
            if not all([bodega_id, pasillo, estante, nivel]):
                return JsonResponse({
                    'error': 'Todos los campos son requeridos'
                }, status=400)
            
            bodega = get_object_or_404(Bodega, id=bodega_id)
            
            ubicacion = UbicacionBodega.objects.create(
                bodega=bodega,
                pasillo=pasillo,
                estante=estante,
                nivel=nivel,
                capacidad_total=capacidad_total,
                capacidad_disponible=capacidad_total
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Ubicación creada exitosamente',
                'ubicacion': {
                    'id': ubicacion.pk,
                    'bodega': ubicacion.bodega.nombre,
                    'pasillo': ubicacion.pasillo,
                    'estante': ubicacion.estante,
                    'nivel': ubicacion.nivel,
                    'capacidad_total': ubicacion.capacidad_total,
                    'capacidad_disponible': ubicacion.capacidad_disponible
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        bodegas = Bodega.objects.all()
        return render(request, 'inventario/ubicaciones/crear.html', {'bodegas': bodegas})

def actualizar_ubicacion_bodega(request, ubicacion_id):
    """
    Vista para actualizar una ubicación de bodega.
    """
    ubicacion = get_object_or_404(UbicacionBodega, id=ubicacion_id)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            ubicacion.pasillo = data.get('pasillo', ubicacion.pasillo)
            ubicacion.estante = data.get('estante', ubicacion.estante)
            ubicacion.nivel = data.get('nivel', ubicacion.nivel)
            
            if 'capacidad_total' in data:
                nueva_capacidad = int(data['capacidad_total'])
                diferencia = nueva_capacidad - ubicacion.capacidad_total
                ubicacion.capacidad_total = nueva_capacidad
                ubicacion.capacidad_disponible += diferencia
            
            ubicacion.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Ubicación actualizada exitosamente',
                'ubicacion': {
                    'id': ubicacion.pk,
                    'pasillo': ubicacion.pasillo,
                    'estante': ubicacion.estante,
                    'nivel': ubicacion.nivel,
                    'capacidad_total': ubicacion.capacidad_total,
                    'capacidad_disponible': ubicacion.capacidad_disponible
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    elif request.method == 'GET':
        return render(request, 'inventario/ubicaciones/editar.html', {'ubicacion': ubicacion})

def eliminar_ubicacion_bodega(request, ubicacion_id):
    """
    Vista para eliminar una ubicación de bodega.
    """
    if request.method == 'DELETE':
        try:
            ubicacion = get_object_or_404(UbicacionBodega, id=ubicacion_id)
            descripcion = str(ubicacion)
            ubicacion.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Ubicación "{descripcion}" eliminada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# =========================
# VISTAS DE PEDIDOS
# =========================

class PedidoListView(ListView):
    """
    Vista para listar pedidos con filtros por estado.
    Permite ver pedidos por diferentes estados y fechas.
    """
    model = Pedido
    template_name = 'inventario/pedidos/lista.html'
    context_object_name = 'pedidos'
    paginate_by = 15

    def get_queryset(self):
        queryset = Pedido.objects.select_related('cliente').all()
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Pedido.ESTADOS_PEDIDO
        context['estado_actual'] = self.request.GET.get('estado', '')
        return context

class PedidoDetailView(DetailView):
    """
    Vista detallada de un pedido específico.
    Muestra productos, total y estado actual.
    """
    model = Pedido
    template_name = 'inventario/pedidos/detalle.html'
    context_object_name = 'pedido'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = PedidoProducto.objects.filter(pedido=self.object) # type: ignore
        context['total'] = self.object.calcular_total() # type: ignore
        return context

@jwt_required
@require_permission('can_manage_orders')
def crear_pedido(request):
    """
    Vista para crear un nuevo pedido.
    Maneja la creación de pedidos con múltiples productos.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            productos_data = data.get('productos', [])
            
            cliente = get_object_or_404(Cliente, id=cliente_id)
            
            # Generar número de pedido único
            ultimo_pedido = Pedido.objects.order_by('-id').first()
            numero_pedido = f"PED-{(ultimo_pedido.id + 1 if ultimo_pedido else 1):06d}" # type: ignore
            
            # Crear pedido
            pedido = Pedido.objects.create(
                numero_pedido=numero_pedido,
                cliente=cliente,
                estado='pendiente'
            )
            
            # Agregar productos al pedido
            for producto_data in productos_data:
                producto = get_object_or_404(Producto, id=producto_data['producto_id'])
                cantidad = int(producto_data['cantidad'])
                
                # Verificar stock disponible
                if producto.cantidad_stock >= cantidad:
                    PedidoProducto.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio_venta
                    )
                    # Reducir stock
                    producto.reducir_stock(cantidad)
                else:
                    return JsonResponse({
                        'error': f'Stock insuficiente para {producto.nombre}'
                    }, status=400)
            
            return JsonResponse({
                'success': True,
                'pedido_id': pedido.id, # type: ignore
                'numero_pedido': pedido.numero_pedido
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    # GET request - mostrar formulario
    clientes = Cliente.objects.all()
    productos = Producto.objects.filter(cantidad_stock__gt=0)
    return render(request, 'inventario/pedidos/crear.html', {
        'clientes': clientes,
        'productos': productos
    })

@csrf_exempt
@jwt_required
@require_permission('can_manage_orders')
def actualizar_estado_pedido(request, pedido_id):
    """
    Vista para actualizar el estado de un pedido.
    Maneja las transiciones de estado válidas.
    """
    if request.method in ['POST', 'PUT']:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        if request.method == 'PUT':
            import json
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
        else:
            nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in [estado[0] for estado in Pedido.ESTADOS_PEDIDO]:
            pedido.estado = nuevo_estado
            if nuevo_estado == 'entregado':
                pedido.marcar_completado()
            else:
                pedido.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estado del pedido actualizado a {nuevo_estado}',
                'pedido': {
                    'id': pedido.pk,
                    'numero_pedido': pedido.numero_pedido,
                    'estado': pedido.estado
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Estado inválido'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

@csrf_exempt
@jwt_required
@require_permission('can_manage_orders')
def api_actualizar_pedido(request, pedido_id):
    """
    API endpoint para actualizar un pedido específico por ID.
    Maneja actualizaciones completas con PUT.
    """
    if request.method == 'PUT':
        try:
            pedido = get_object_or_404(Pedido, id=pedido_id)
            data = json.loads(request.body)
            
            # Actualizar campos permitidos
            if 'estado' in data:
                nuevo_estado = data['estado']
                if nuevo_estado in [estado[0] for estado in Pedido.ESTADOS_PEDIDO]:
                    pedido.estado = nuevo_estado
                    if nuevo_estado == 'entregado':
                        pedido.marcar_completado()
                else:
                    return JsonResponse({
                        'error': f'Estado inválido: {nuevo_estado}'
                    }, status=400)
            
            if 'cliente_id' in data:
                try:
                    nuevo_cliente = Cliente.objects.get(id=data['cliente_id'])
                    pedido.cliente = nuevo_cliente
                except Cliente.DoesNotExist:
                    return JsonResponse({
                        'error': 'Cliente no encontrado'
                    }, status=404)
            
            # Guardar cambios
            pedido.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Pedido actualizado exitosamente',
                'pedido': {
                    'id': pedido.pk,
                    'numero_pedido': pedido.numero_pedido,
                    'estado': pedido.estado,
                    'cliente_id': pedido.cliente.pk,
                    'fecha_creacion': pedido.fecha_creacion.isoformat(),
                    'fecha_completado': pedido.fecha_completado.isoformat() if pedido.fecha_completado else None
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        # Obtener detalles de un pedido específico
        try:
            pedido = get_object_or_404(Pedido, id=pedido_id)
            
            return JsonResponse({
                'success': True,
                'pedido': {
                    'id': pedido.pk,
                    'numero_pedido': pedido.numero_pedido,
                    'estado': pedido.estado,
                    'fecha_creacion': pedido.fecha_creacion.isoformat(),
                    'fecha_completado': pedido.fecha_completado.isoformat() if pedido.fecha_completado else None,
                    'cliente': {
                        'id': pedido.cliente.pk,
                        'nombre': pedido.cliente.nombre,
                        'email': pedido.cliente.email
                    },
                    'total': float(pedido.calcular_total()),
                    'total_productos': PedidoProducto.objects.filter(pedido=pedido).count(),
                    'puede_cancelar': pedido.puede_cancelar()
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

# =========================
# VISTAS DE CLIENTES
# =========================

class ClienteListView(ListView):
    """
    Vista para listar todos los clientes del sistema.
    """
    model = Cliente
    template_name = 'inventario/clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 20

class ClienteDetailView(DetailView):
    """
    Vista detallada de un cliente específico.
    Muestra información y historial de pedidos.
    """
    model = Cliente
    template_name = 'inventario/clientes/detalle.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pedidos'] = Pedido.objects.filter(cliente=self.object).order_by('-fecha_creacion')[:10] # type: ignore
        return context

@jwt_required
@require_permission('can_manage_clients')
def crear_cliente(request):
    """
    Vista para crear un nuevo cliente.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            nombre = data.get('nombre')
            email = data.get('email')
            telefono = data.get('telefono', '')
            direccion = data.get('direccion', '')
            ciudad = data.get('ciudad', '')
            
            if not nombre or not email:
                return JsonResponse({
                    'error': 'Nombre y email son requeridos'
                }, status=400)
            
            # Verificar que el email no exista
            if Cliente.objects.filter(email=email).exists():
                return JsonResponse({
                    'error': f'Ya existe un cliente con email: {email}'
                }, status=400)
            
            cliente = Cliente.objects.create(
                nombre=nombre,
                email=email,
                telefono=telefono,
                direccion=direccion,
                ciudad=ciudad
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Cliente creado exitosamente',
                'cliente': {
                    'id': cliente.pk,
                    'nombre': cliente.nombre,
                    'email': cliente.email,
                    'telefono': cliente.telefono,
                    'direccion': cliente.direccion,
                    'ciudad': cliente.ciudad
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return render(request, 'inventario/clientes/crear.html')

def actualizar_cliente(request, cliente_id):
    """
    Vista para actualizar un cliente existente.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            cliente.nombre = data.get('nombre', cliente.nombre)
            nuevo_email = data.get('email', cliente.email)
            
            # Verificar email único si se está cambiando
            if nuevo_email != cliente.email:
                if Cliente.objects.filter(email=nuevo_email).exists():
                    return JsonResponse({
                        'error': f'Ya existe un cliente con email: {nuevo_email}'
                    }, status=400)
                cliente.email = nuevo_email
            
            cliente.telefono = data.get('telefono', cliente.telefono)
            cliente.direccion = data.get('direccion', cliente.direccion)
            cliente.ciudad = data.get('ciudad', cliente.ciudad)
            
            cliente.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cliente actualizado exitosamente',
                'cliente': {
                    'id': cliente.pk,
                    'nombre': cliente.nombre,
                    'email': cliente.email,
                    'telefono': cliente.telefono,
                    'direccion': cliente.direccion,
                    'ciudad': cliente.ciudad
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    elif request.method == 'GET':
        return render(request, 'inventario/clientes/editar.html', {'cliente': cliente})

def eliminar_cliente(request, cliente_id):
    """
    Vista para eliminar un cliente.
    """
    if request.method == 'DELETE':
        try:
            cliente = get_object_or_404(Cliente, id=cliente_id)
            
            # Verificar si tiene pedidos asociados
            if Pedido.objects.filter(cliente=cliente).exists():
                return JsonResponse({
                    'error': 'No se puede eliminar el cliente porque tiene pedidos asociados'
                }, status=400)
            
            nombre = cliente.nombre
            cliente.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Cliente "{nombre}" eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# =========================
# CRUD ARTÍCULOS
# =========================

def crear_articulo(request):
    """
    Vista para crear un nuevo artículo.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            producto_id = data.get('producto_id')
            codigo_barras = data.get('codigo_barras')
            ubicacion_id = data.get('ubicacion_id')
            
            if not all([producto_id, codigo_barras, ubicacion_id]):
                return JsonResponse({
                    'error': 'Producto, código de barras y ubicación son requeridos'
                }, status=400)
            
            # Verificar que el código de barras no exista
            if Articulo.objects.filter(codigo_barras=codigo_barras).exists():
                return JsonResponse({
                    'error': f'Ya existe un artículo con código de barras: {codigo_barras}'
                }, status=400)
            
            producto = get_object_or_404(Producto, id=producto_id)
            ubicacion = get_object_or_404(UbicacionBodega, id=ubicacion_id)
            
            # Verificar disponibilidad en ubicación
            if not ubicacion.ocupar_espacio(1):
                return JsonResponse({
                    'error': 'No hay espacio disponible en la ubicación seleccionada'
                }, status=400)
            
            articulo = Articulo.objects.create(
                producto=producto,
                codigo_barras=codigo_barras,
                ubicacion=ubicacion
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Artículo creado exitosamente',
                'articulo': {
                    'id': articulo.pk,
                    'producto': articulo.producto.nombre,
                    'codigo_barras': articulo.codigo_barras,
                    'fecha_ingreso': articulo.fecha_ingreso.isoformat(),
                    'ubicacion': str(articulo.ubicacion)
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        productos = Producto.objects.all()
        ubicaciones = UbicacionBodega.objects.all()
        return render(request, 'inventario/articulos/crear.html', {
            'productos': productos,
            'ubicaciones': ubicaciones
        })

def actualizar_articulo(request, articulo_id):
    """
    Vista para actualizar un artículo existente.
    """
    articulo = get_object_or_404(Articulo, id=articulo_id)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            nuevo_codigo = data.get('codigo_barras', articulo.codigo_barras)
            nueva_ubicacion_id = data.get('ubicacion_id')
            
            # Verificar código único si se está cambiando
            if nuevo_codigo != articulo.codigo_barras:
                if Articulo.objects.filter(codigo_barras=nuevo_codigo).exists():
                    return JsonResponse({
                        'error': f'Ya existe un artículo con código: {nuevo_codigo}'
                    }, status=400)
                articulo.codigo_barras = nuevo_codigo
            
            # Cambiar ubicación si se especifica
            if nueva_ubicacion_id and str(nueva_ubicacion_id) != str(articulo.ubicacion.pk):
                ubicacion_anterior = articulo.ubicacion
                nueva_ubicacion = get_object_or_404(UbicacionBodega, id=nueva_ubicacion_id)
                
                # Verificar disponibilidad en nueva ubicación
                if nueva_ubicacion.ocupar_espacio(1):
                    # Liberar espacio en ubicación anterior
                    ubicacion_anterior.capacidad_disponible += 1
                    ubicacion_anterior.save()
                    articulo.ubicacion = nueva_ubicacion
                else:
                    return JsonResponse({
                        'error': 'No hay espacio disponible en la nueva ubicación'
                    }, status=400)
            
            articulo.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Artículo actualizado exitosamente',
                'articulo': {
                    'id': articulo.pk,
                    'codigo_barras': articulo.codigo_barras,
                    'ubicacion': str(articulo.ubicacion)
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    elif request.method == 'GET':
        ubicaciones = UbicacionBodega.objects.all()
        return render(request, 'inventario/articulos/editar.html', {
            'articulo': articulo,
            'ubicaciones': ubicaciones
        })

def eliminar_articulo(request, articulo_id):
    """
    Vista para eliminar un artículo.
    """
    if request.method == 'DELETE':
        try:
            articulo = get_object_or_404(Articulo, id=articulo_id)
            
            # Liberar espacio en la ubicación
            ubicacion = articulo.ubicacion
            ubicacion.capacidad_disponible += 1
            ubicacion.save()
            
            codigo_barras = articulo.codigo_barras
            articulo.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Artículo "{codigo_barras}" eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# =========================
# CRUD USUARIOS
# =========================

def crear_usuario(request):
    """
    Vista para crear un nuevo usuario.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            nombre_usuario = data.get('nombre_usuario')
            email = data.get('email')
            telefono = data.get('telefono', '')
            rol = data.get('rol', 'empleado')
            
            if not nombre_usuario or not email:
                return JsonResponse({
                    'error': 'Nombre de usuario y email son requeridos'
                }, status=400)
            
            # Verificar unicidad
            if Usuario.objects.filter(nombre_usuario=nombre_usuario).exists():
                return JsonResponse({
                    'error': f'Ya existe un usuario con nombre: {nombre_usuario}'
                }, status=400)
            
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse({
                    'error': f'Ya existe un usuario con email: {email}'
                }, status=400)
            
            usuario = Usuario.objects.create(
                nombre_usuario=nombre_usuario,
                email=email,
                telefono=telefono,
                rol=rol
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Usuario creado exitosamente',
                'usuario': {
                    'id': usuario.pk,
                    'nombre_usuario': usuario.nombre_usuario,
                    'email': usuario.email,
                    'telefono': usuario.telefono,
                    'rol': usuario.rol,
                    'fecha_creacion': usuario.fecha_creacion.isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return render(request, 'inventario/usuarios/crear.html', {
            'roles': Usuario.ROLES_USUARIO
        })

def actualizar_usuario(request, usuario_id):
    """
    Vista para actualizar un usuario existente.
    """
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            nuevo_nombre = data.get('nombre_usuario', usuario.nombre_usuario)
            nuevo_email = data.get('email', usuario.email)
            
            # Verificar unicidad si se están cambiando
            if nuevo_nombre != usuario.nombre_usuario:
                if Usuario.objects.filter(nombre_usuario=nuevo_nombre).exists():
                    return JsonResponse({
                        'error': f'Ya existe un usuario con nombre: {nuevo_nombre}'
                    }, status=400)
                usuario.nombre_usuario = nuevo_nombre
            
            if nuevo_email != usuario.email:
                if Usuario.objects.filter(email=nuevo_email).exists():
                    return JsonResponse({
                        'error': f'Ya existe un usuario con email: {nuevo_email}'
                    }, status=400)
                usuario.email = nuevo_email
            
            usuario.telefono = data.get('telefono', usuario.telefono)
            usuario.rol = data.get('rol', usuario.rol)
            
            usuario.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Usuario actualizado exitosamente',
                'usuario': {
                    'id': usuario.pk,
                    'nombre_usuario': usuario.nombre_usuario,
                    'email': usuario.email,
                    'telefono': usuario.telefono,
                    'rol': usuario.rol
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    elif request.method == 'GET':
        return render(request, 'inventario/usuarios/editar.html', {
            'usuario': usuario,
            'roles': Usuario.ROLES_USUARIO
        })

def eliminar_usuario(request, usuario_id):
    """
    Vista para eliminar un usuario.
    """
    if request.method == 'DELETE':
        try:
            usuario = get_object_or_404(Usuario, id=usuario_id)
            nombre = usuario.nombre_usuario
            usuario.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Usuario "{nombre}" eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# =========================
# VISTAS DE REPORTES
# =========================

def reporte_inventario(request):
    """
    Vista que genera reporte general de inventario.
    Incluye productos, stock y valores totales.
    """
    productos = Producto.objects.all()
    
    # Calcular estadísticas
    valor_total_inventario = sum(
        p.precio_costo * p.cantidad_stock for p in productos
    )
    
    productos_criticos = productos.filter(cantidad_stock__lte=5)
    
    context = {
        'productos': productos,
        'valor_total_inventario': valor_total_inventario,
        'productos_criticos': productos_criticos,
        'total_productos': productos.count(),
    }
    
    return render(request, 'inventario/reportes/inventario.html', context)

def reporte_ventas(request):
    """
    Vista que genera reporte de ventas por período.
    Muestra estadísticas de pedidos y facturación.
    """
    # Filtros de fecha (último mes por defecto)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin.replace(day=1)  # Primer día del mes actual
    
    pedidos = Pedido.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin
    )
    
    # Calcular totales
    total_pedidos = pedidos.count()
    pedidos_completados = pedidos.filter(estado='entregado').count()
    
    # Calcular ingresos totales
    ingresos_totales = Decimal('0.00')
    for pedido in pedidos.filter(estado='entregado'):
        ingresos_totales += pedido.calcular_total()
    
    context = {
        'pedidos': pedidos.order_by('-fecha_creacion'),
        'total_pedidos': total_pedidos,
        'pedidos_completados': pedidos_completados,
        'ingresos_totales': ingresos_totales,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/reportes/ventas.html', context)

# =========================
# VISTAS API (JSON)
# =========================

def api_productos_stock(request):
    """
    API endpoint que retorna productos con sus niveles de stock.
    Útil para integraciones y actualizaciones en tiempo real.
    """
    productos = Producto.objects.all().values(
        'id', 'nombre', 'cantidad_stock', 'precio_venta'
    )
    return JsonResponse(list(productos), safe=False)

def api_buscar_productos(request):
    """
    API endpoint para búsqueda de productos.
    Retorna productos que coincidan con el término de búsqueda.
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    productos = Producto.objects.filter(
        Q(nombre__icontains=query) | Q(marca__icontains=query)
    ).values('id', 'nombre', 'precio_venta', 'cantidad_stock')[:10]
    
    return JsonResponse(list(productos), safe=False)

def api_pedido_total(request, pedido_id):
    """
    API endpoint que calcula el total de un pedido específico.
    """
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        total = pedido.calcular_total()
        return JsonResponse({
            'pedido_id': pedido_id,
            'total': float(total),
            'estado': pedido.estado
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_articulos(request):
    """
    API endpoint para listar todos los artículos del sistema.
    Incluye paginación y filtros opcionales.
    """
    try:
        # Parámetros de consulta opcionales
        limit = int(request.GET.get('limit', 100))  # Límite por defecto: 100
        offset = int(request.GET.get('offset', 0))   # Offset por defecto: 0
        producto_id = request.GET.get('producto_id')
        ubicacion_id = request.GET.get('ubicacion_id')
        codigo_barras = request.GET.get('codigo_barras')
        
        # Construir queryset base
        queryset = Articulo.objects.select_related('producto', 'ubicacion', 'ubicacion__bodega').all()
        
        # Aplicar filtros si se proporcionan
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        
        if ubicacion_id:
            queryset = queryset.filter(ubicacion_id=ubicacion_id)
            
        if codigo_barras:
            queryset = queryset.filter(codigo_barras__icontains=codigo_barras)
        
        # Contar total antes de paginación
        total_count = queryset.count()
        
        # Aplicar paginación
        articulos = queryset[offset:offset + limit]
        
        # Construir respuesta JSON
        articulos_data = []
        for articulo in articulos:
            articulo_info = {
                'id': articulo.pk,
                'codigo_barras': articulo.codigo_barras,
                'fecha_ingreso': articulo.fecha_ingreso.isoformat(),
                'fecha_salida': articulo.fecha_salida.isoformat() if articulo.fecha_salida else None,
                'producto': {
                    'id': articulo.producto.pk,
                    'nombre': articulo.producto.nombre,
                    'marca': articulo.producto.marca,
                    'precio_venta': float(articulo.producto.precio_venta),
                    'color': articulo.producto.color,
                    'talla': articulo.producto.talla
                },
                'ubicacion': {
                    'id': articulo.ubicacion.pk,
                    'pasillo': articulo.ubicacion.pasillo,
                    'estante': articulo.ubicacion.estante,
                    'nivel': articulo.ubicacion.nivel,
                    'bodega': {
                        'id': articulo.ubicacion.bodega.pk,
                        'nombre': articulo.ubicacion.bodega.nombre,
                        'ciudad': articulo.ubicacion.bodega.ciudad
                    }
                }
            }
            articulos_data.append(articulo_info)
        
        # Calcular información de paginación
        has_next = (offset + limit) < total_count
        has_previous = offset > 0
        
        return JsonResponse({
            'success': True,
            'count': len(articulos_data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_next': has_next,
            'has_previous': has_previous,
            'articulos': articulos_data
        })
        
    except ValueError as e:
        return JsonResponse({
            'error': f'Parámetros inválidos: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)

# =========================
# APIs PARA LISTAR TODOS LOS MODELOS
# =========================

@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_productos(request):
    """
    API endpoint para listar todos los productos del sistema.
    GET: Incluye paginación y filtros opcionales.
    POST: Crear nuevo producto.
    """
    if request.method == 'GET':
        try:
            # Parámetros de consulta
            limit = int(request.GET.get('limit', 100))
            offset = int(request.GET.get('offset', 0))
            marca = request.GET.get('marca')
            precio_min = request.GET.get('precio_min')
            precio_max = request.GET.get('precio_max')
            sin_stock = request.GET.get('sin_stock', '').lower() == 'true'
            
            # Construir queryset
            queryset = Producto.objects.all()
            
            # Aplicar filtros
            if marca:
                queryset = queryset.filter(marca__icontains=marca)
            if precio_min:
                queryset = queryset.filter(precio_venta__gte=float(precio_min))
            if precio_max:
                queryset = queryset.filter(precio_venta__lte=float(precio_max))
            if sin_stock:
                queryset = queryset.filter(cantidad_stock=0)
            
            total_count = queryset.count()
            productos = queryset[offset:offset + limit]
            
            productos_data = []
            for producto in productos:
                producto_info = {
                    'id': producto.pk,
                    'nombre': producto.nombre,
                    'descripcion': producto.descripcion,
                    'marca': producto.marca,
                    'precio_costo': float(producto.precio_costo),
                    'precio_venta': float(producto.precio_venta),
                    'cantidad_stock': producto.cantidad_stock,
                    'peso': float(producto.peso),
                    'dimensiones': producto.dimensiones,
                    'color': producto.color,
                    'talla': producto.talla,
                    'margen_ganancia': float(producto.calcular_margen_ganancia()),
                    'hay_stock': producto.hay_stock()
                }
                productos_data.append(producto_info)
            
            return JsonResponse({
                'success': True,
                'count': len(productos_data),
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_next': (offset + limit) < total_count,
                'has_previous': offset > 0,
                'productos': productos_data
            })
            
        except ValueError as e:
            return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    elif request.method == 'POST':
        # Solo usuarios con permiso de gestionar inventario pueden crear productos
        from inventario.auth_utils import has_permission
        if not has_permission(request.user, 'can_manage_inventory'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para crear productos',
                'code': 'PERMISSION_DENIED'
            }, status=403)
        
        try:
            # Obtener datos del request
            data = json.loads(request.body)
            
            # Validar campos requeridos
            required_fields = ['nombre', 'sku', 'precio']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return JsonResponse({
                    'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
                }, status=400)
            
            # Crear el producto
            producto = Producto.objects.create(
                nombre=data['nombre'],
                marca=data.get('marca', ''),
                descripcion=data.get('descripcion', ''),
                precio_costo=Decimal(str(data.get('precio_costo', data['precio']))),
                precio_venta=Decimal(str(data['precio'])),
                cantidad_stock=data.get('stock', 0),
                peso=Decimal(str(data.get('peso', '0.0'))),
                dimensiones=data.get('dimensiones', ''),
                color=data.get('color', ''),
                talla=data.get('talla', ''),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Producto creado exitosamente',
                'producto': {
                    'id': producto.pk,
                    'nombre': producto.nombre,
                    'marca': producto.marca,
                    'precio_venta': float(producto.precio_venta),
                    'cantidad_stock': producto.cantidad_stock,
                    'descripcion': producto.descripcion
                }
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': f'Valores inválidos: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_bodegas(request):
    """
    API endpoint para listar todas las bodegas del sistema.
    """
    try:
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        ciudad = request.GET.get('ciudad')
        
        queryset = Bodega.objects.all()
        
        if ciudad:
            queryset = queryset.filter(ciudad__icontains=ciudad)
        
        total_count = queryset.count()
        bodegas = queryset[offset:offset + limit]
        
        bodegas_data = []
        for bodega in bodegas:
            bodega_info = {
                'id': bodega.pk,
                'nombre': bodega.nombre,
                'ciudad': bodega.ciudad,
                'direccion': bodega.direccion,
                'capacidad_total': bodega.obtener_capacidad_total(),
                'total_ubicaciones': UbicacionBodega.objects.filter(bodega=bodega).count()
            }
            bodegas_data.append(bodega_info)
        
        return JsonResponse({
            'success': True,
            'count': len(bodegas_data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
            'bodegas': bodegas_data
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_ubicaciones(request):
    """
    API endpoint para listar todas las ubicaciones de bodega.
    """
    try:
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        bodega_id = request.GET.get('bodega_id')
        pasillo = request.GET.get('pasillo')
        disponible = request.GET.get('disponible', '').lower() == 'true'
        
        queryset = UbicacionBodega.objects.select_related('bodega').all()
        
        if bodega_id:
            queryset = queryset.filter(bodega_id=bodega_id)
        if pasillo:
            queryset = queryset.filter(pasillo__icontains=pasillo)
        if disponible:
            queryset = queryset.filter(capacidad_disponible__gt=0)
        
        total_count = queryset.count()
        ubicaciones = queryset[offset:offset + limit]
        
        ubicaciones_data = []
        for ubicacion in ubicaciones:
            ubicacion_info = {
                'id': ubicacion.pk,
                'bodega': {
                    'id': ubicacion.bodega.pk,
                    'nombre': ubicacion.bodega.nombre,
                    'ciudad': ubicacion.bodega.ciudad
                },
                'pasillo': ubicacion.pasillo,
                'estante': ubicacion.estante,
                'nivel': ubicacion.nivel,
                'capacidad_total': ubicacion.capacidad_total,
                'capacidad_disponible': ubicacion.capacidad_disponible,
                'capacidad_ocupada': ubicacion.capacidad_total - ubicacion.capacidad_disponible,
                'porcentaje_ocupacion': round(((ubicacion.capacidad_total - ubicacion.capacidad_disponible) / ubicacion.capacidad_total * 100) if ubicacion.capacidad_total > 0 else 0, 2),
                'esta_llena': ubicacion.esta_llena(),
                'total_articulos': Articulo.objects.filter(ubicacion=ubicacion).count()
            }
            ubicaciones_data.append(ubicacion_info)
        
        return JsonResponse({
            'success': True,
            'count': len(ubicaciones_data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
            'ubicaciones': ubicaciones_data
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@csrf_exempt
@csrf_exempt
@jwt_required
def api_listar_clientes(request):
    """
    API endpoint para listar todos los clientes del sistema (GET) y crear nuevos clientes (POST).
    """
    if request.method == 'GET':
        try:
            # Verificar permisos para listar
            from .auth_utils import has_permission
            if not has_permission(request.user, 'can_view_all_data'):
                return JsonResponse({'error': 'Sin permisos para ver clientes'}, status=403)
            
            limit = int(request.GET.get('limit', 100))
            offset = int(request.GET.get('offset', 0))
            ciudad = request.GET.get('ciudad')
            email = request.GET.get('email')
            
            queryset = Cliente.objects.all()
            
            if ciudad:
                queryset = queryset.filter(ciudad__icontains=ciudad)
            if email:
                queryset = queryset.filter(email__icontains=email)
            
            total_count = queryset.count()
            clientes = queryset[offset:offset + limit]
            
            clientes_data = []
            for cliente in clientes:
                cliente_info = {
                    'id': cliente.pk,
                    'nombre': cliente.nombre,
                    'email': cliente.email,
                    'telefono': cliente.telefono,
                    'direccion': cliente.direccion,
                    'ciudad': cliente.ciudad,
                    'total_pedidos': Pedido.objects.filter(cliente=cliente).count(),
                    'pedidos_pendientes': Pedido.objects.filter(cliente=cliente, estado='pendiente').count()
                }
                clientes_data.append(cliente_info)
            
            return JsonResponse({
                'success': True,
                'count': len(clientes_data),
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_next': (offset + limit) < total_count,
                'has_previous': offset > 0,
                'clientes': clientes_data
            })
            
        except ValueError as e:
            return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    elif request.method == 'POST':
        import json
        try:
            # Verificar permisos para crear
            from .auth_utils import get_user_role
            user_role = get_user_role(request.user)
            if user_role not in ['admin', 'gerente']:
                return JsonResponse({'error': 'Sin permisos para crear clientes'}, status=403)
            
            data = json.loads(request.body)
            
            # Validar campos requeridos
            required_fields = ['nombre', 'email', 'telefono', 'direccion', 'ciudad']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({'error': f'Campo requerido: {field}'}, status=400)
            
            # Verificar que el email no exista
            if Cliente.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Ya existe un cliente con ese email'}, status=400)
            
            # Crear el cliente
            cliente = Cliente.objects.create(
                nombre=data['nombre'],
                email=data['email'],
                telefono=data['telefono'],
                direccion=data['direccion'],
                ciudad=data['ciudad']
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Cliente creado exitosamente',
                'cliente': {
                    'id': cliente.pk,
                    'nombre': cliente.nombre,
                    'email': cliente.email,
                    'telefono': cliente.telefono,
                    'direccion': cliente.direccion,
                    'ciudad': cliente.ciudad
                }
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@jwt_required
@require_roles('admin', 'gerente')
def api_listar_usuarios(request):
    """
    API endpoint para listar todos los usuarios del sistema.
    """
    try:
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        rol = request.GET.get('rol')
        
        queryset = Usuario.objects.all()
        
        if rol:
            queryset = queryset.filter(rol=rol)
        
        total_count = queryset.count()
        usuarios = queryset[offset:offset + limit]
        
        usuarios_data = []
        for usuario in usuarios:
            usuario_info = {
                'id': usuario.pk,
                'nombre_usuario': usuario.nombre_usuario,
                'email': usuario.email,
                'telefono': usuario.telefono,
                'rol': usuario.rol,
                'fecha_creacion': usuario.fecha_creacion.isoformat(),
                'ultimo_acceso': usuario.ultimo_acceso.isoformat()
            }
            usuarios_data.append(usuario_info)
        
        return JsonResponse({
            'success': True,
            'count': len(usuarios_data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
            'usuarios': usuarios_data
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@csrf_exempt
@jwt_required
@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_pedidos(request):
    """
    API endpoint para listar todos los pedidos del sistema y crear nuevos pedidos.
    GET: Lista pedidos con filtros y paginación
    POST: Crea un nuevo pedido
    """
    if request.method == 'GET':
        try:
            limit = int(request.GET.get('limit', 100))
            offset = int(request.GET.get('offset', 0))
            estado = request.GET.get('estado')
            cliente_id = request.GET.get('cliente_id')
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            queryset = Pedido.objects.select_related('cliente').all()
            
            if estado:
                queryset = queryset.filter(estado=estado)
            if cliente_id:
                queryset = queryset.filter(cliente_id=cliente_id)
            if fecha_inicio:
                queryset = queryset.filter(fecha_creacion__date__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha_creacion__date__lte=fecha_fin)
            
            total_count = queryset.count()
            pedidos = queryset.order_by('-fecha_creacion')[offset:offset + limit]
            
            pedidos_data = []
            for pedido in pedidos:
                pedido_info = {
                    'id': pedido.pk,
                    'numero_pedido': pedido.numero_pedido,
                    'estado': pedido.estado,
                    'fecha_creacion': pedido.fecha_creacion.isoformat(),
                    'fecha_completado': pedido.fecha_completado.isoformat() if pedido.fecha_completado else None,
                    'cliente': {
                        'id': pedido.cliente.pk,
                        'nombre': pedido.cliente.nombre,
                        'email': pedido.cliente.email
                    },
                    'total': float(pedido.calcular_total()),
                    'total_productos': PedidoProducto.objects.filter(pedido=pedido).count(),
                    'puede_cancelar': pedido.puede_cancelar(),
                    'cotizacion_id': pedido.cotizacion.pk if pedido.cotizacion else None
                }
                pedidos_data.append(pedido_info)
            
            return JsonResponse({
                'success': True,
                'count': len(pedidos_data),
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_next': (offset + limit) < total_count,
                'has_previous': offset > 0,
                'pedidos': pedidos_data
            })
            
        except ValueError as e:
            return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    elif request.method == 'POST':
        # Solo usuarios con permiso de gestionar pedidos pueden crear
        from inventario.auth_utils import has_permission
        if not has_permission(request.user, 'can_manage_orders'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para crear pedidos',
                'code': 'PERMISSION_DENIED'
            }, status=403)
        
        try:
            import json
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            estado = data.get('estado', 'pendiente')
            observaciones = data.get('observaciones', '')
            
            # Validar cliente existe
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                return JsonResponse({
                    'error': 'Cliente no encontrado'
                }, status=404)
            
            # Generar número de pedido único
            ultimo_pedido = Pedido.objects.order_by('-id').first()
            numero_pedido = f"PED-{(ultimo_pedido.pk + 1 if ultimo_pedido else 1):06d}"
            
            # Crear pedido
            pedido = Pedido.objects.create(
                numero_pedido=numero_pedido,
                cliente=cliente,
                estado=estado
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Pedido creado exitosamente',
                'pedido': {
                    'id': pedido.pk,
                    'numero_pedido': pedido.numero_pedido,
                    'estado': pedido.estado,
                    'cliente_id': cliente.pk,
                    'fecha_creacion': pedido.fecha_creacion.isoformat()
                }
            }, status=201)
            
        except Exception as e:
            if 'JSON' in str(e) or 'json' in str(e).lower():
                return JsonResponse({'error': 'JSON inválido'}, status=400)
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_cotizaciones(request):
    """
    API endpoint para listar todas las cotizaciones del sistema.
    """
    try:
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        cliente_id = request.GET.get('cliente_id')
        estado = request.GET.get('estado')
        vigente = request.GET.get('vigente', '').lower() == 'true'
        
        queryset = Cotizacion.objects.select_related('cliente').all()
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if vigente:
            queryset = queryset.filter(validez_hasta__gte=timezone.now())
        
        total_count = queryset.count()
        cotizaciones = queryset.order_by('-fecha_creacion')[offset:offset + limit]
        
        cotizaciones_data = []
        for cotizacion in cotizaciones:
            cotizacion_info = {
                'id': cotizacion.pk,
                'cliente': {
                    'id': cotizacion.cliente.pk,
                    'nombre': cotizacion.cliente.nombre,
                    'email': cotizacion.cliente.email
                },
                'fecha_creacion': cotizacion.fecha_creacion.isoformat(),
                'validez_hasta': cotizacion.validez_hasta.isoformat(),
                'total': float(cotizacion.total),
                'estado': cotizacion.estado,
                'esta_vigente': cotizacion.esta_vigente(),
                'tiene_pedido': Pedido.objects.filter(cotizacion=cotizacion).exists()
            }
            cotizaciones_data.append(cotizacion_info)
        
        return JsonResponse({
            'success': True,
            'count': len(cotizaciones_data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
            'cotizaciones': cotizaciones_data
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@csrf_exempt
@jwt_required
@require_permission('can_view_all_data')
def api_listar_facturas(request):
    """
    API endpoint para listar todas las facturas del sistema.
    """
    try:
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        metodo_pago = request.GET.get('metodo_pago')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        queryset = Factura.objects.select_related('pedido', 'pedido__cliente').all()
        
        if metodo_pago:
            queryset = queryset.filter(metodo_pago__icontains=metodo_pago)
        if fecha_inicio:
            queryset = queryset.filter(fecha_emision__date__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha_emision__date__lte=fecha_fin)
        
        total_count = queryset.count()
        facturas = queryset.order_by('-fecha_emision')[offset:offset + limit]
        
        facturas_data = []
        for factura in facturas:
            factura_info = {
                'id': factura.pk,
                'pedido': {
                    'id': factura.pedido.pk,
                    'numero_pedido': factura.pedido.numero_pedido,
                    'cliente': {
                        'id': factura.pedido.cliente.pk,
                        'nombre': factura.pedido.cliente.nombre
                    }
                },
                'fecha_emision': factura.fecha_emision.isoformat(),
                'total': float(factura.total),
                'descuentos': float(factura.descuentos),
                'total_neto': float(factura.calcular_total_neto()),
                'metodo_pago': factura.metodo_pago
            }
            facturas_data.append(factura_info)
        
        return JsonResponse({
            'success': True,
            'count': len(facturas_data),
            'total': total_count,
            'offset': offset,
            'limit': limit,
            'has_next': (offset + limit) < total_count,
            'has_previous': offset > 0,
            'facturas': facturas_data
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

# =========================
# VISTAS BATCH PARA CREACIÓN MASIVA
# =========================

def crear_ubicaciones_batch(request):
    """
    Vista para crear múltiples ubicaciones de bodega en una sola operación.
    Optimizada para creación masiva de inventario.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ubicaciones_data = data.get('ubicaciones', [])
            
            if not ubicaciones_data:
                return JsonResponse({
                    'error': 'Se requiere una lista de ubicaciones'
                }, status=400)
            
            ubicaciones_creadas = []
            errores = []
            
            for ubicacion_data in ubicaciones_data:
                try:
                    bodega_id = ubicacion_data.get('bodega_id')
                    pasillo = ubicacion_data.get('pasillo')
                    estante = ubicacion_data.get('estante') 
                    nivel = ubicacion_data.get('nivel')
                    capacidad_total = int(ubicacion_data.get('capacidad_total', 0))
                    
                    if not all([bodega_id, pasillo, estante, nivel]):
                        errores.append(f'Datos incompletos para ubicación {pasillo}-{estante}')
                        continue
                    
                    bodega = get_object_or_404(Bodega, id=bodega_id)
                    
                    # Verificar si ya existe
                    if UbicacionBodega.objects.filter(
                        bodega=bodega, pasillo=pasillo, estante=estante, nivel=nivel
                    ).exists():
                        errores.append(f'Ubicación {pasillo}-{estante}-{nivel} ya existe')
                        continue
                    
                    ubicacion = UbicacionBodega.objects.create(
                        bodega=bodega,
                        pasillo=pasillo,
                        estante=estante,
                        nivel=nivel,
                        capacidad_total=capacidad_total,
                        capacidad_disponible=capacidad_total
                    )
                    
                    ubicaciones_creadas.append({
                        'id': ubicacion.pk,
                        'pasillo': ubicacion.pasillo,
                        'estante': ubicacion.estante,
                        'nivel': ubicacion.nivel,
                        'capacidad_total': ubicacion.capacidad_total
                    })
                    
                except Exception as e:
                    errores.append(f'Error creando ubicación: {str(e)}')
            
            return JsonResponse({
                'success': True,
                'message': f'Batch procesado: {len(ubicaciones_creadas)} ubicaciones creadas',
                'created_count': len(ubicaciones_creadas),
                'ubicaciones': ubicaciones_creadas,
                'errors': errores,
                'error_count': len(errores)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

def crear_articulos_batch(request):
    """
    Vista para crear múltiples artículos en una sola operación.
    Optimizada para procesamiento masivo de hasta 1000 artículos por request.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            articulos_data = data.get('articulos', [])
            
            if not articulos_data:
                return JsonResponse({
                    'error': 'Se requiere una lista de artículos'
                }, status=400)
            
            # Limitar batch size para evitar timeouts
            if len(articulos_data) > 1000:
                return JsonResponse({
                    'error': 'Máximo 1000 artículos por lote'
                }, status=400)
            
            articulos_creados = []
            errores = []
            codigos_usados = set()  # Para verificar duplicados en el lote
            
            for articulo_data in articulos_data:
                try:
                    producto_id = articulo_data.get('producto_id')
                    codigo_barras = articulo_data.get('codigo_barras')
                    ubicacion_id = articulo_data.get('ubicacion_id')
                    
                    if not all([producto_id, codigo_barras, ubicacion_id]):
                        errores.append('Datos incompletos para un artículo')
                        continue
                    
                    # Verificar duplicados en el lote actual
                    if codigo_barras in codigos_usados:
                        errores.append(f'Código duplicado en lote: {codigo_barras}')
                        continue
                    
                    # Verificar que no exista en la base de datos
                    if Articulo.objects.filter(codigo_barras=codigo_barras).exists():
                        errores.append(f'Código ya existe en BD: {codigo_barras}')
                        continue
                    
                    producto = Producto.objects.filter(id=producto_id).first()
                    ubicacion = UbicacionBodega.objects.filter(id=ubicacion_id).first()
                    
                    if not producto:
                        errores.append(f'Producto {producto_id} no encontrado')
                        continue
                    
                    if not ubicacion:
                        errores.append(f'Ubicación {ubicacion_id} no encontrada') 
                        continue
                    
                    # Verificar capacidad (optimizado - no ocupar aún)
                    if ubicacion.capacidad_disponible <= 0:
                        errores.append(f'Sin capacidad en ubicación {ubicacion_id}')
                        continue
                    
                    # Crear el artículo
                    articulo = Articulo.objects.create(
                        producto=producto,
                        codigo_barras=codigo_barras,
                        ubicacion=ubicacion
                    )
                    
                    # Reducir capacidad disponible
                    ubicacion.capacidad_disponible -= 1
                    ubicacion.save()
                    
                    articulos_creados.append({
                        'id': articulo.pk,
                        'codigo_barras': articulo.codigo_barras,
                        'producto': articulo.producto.nombre,
                        'ubicacion': str(ubicacion)
                    })
                    
                    codigos_usados.add(codigo_barras)
                    
                except Exception as e:
                    errores.append(f'Error creando artículo: {str(e)}')
            
            return JsonResponse({
                'success': True,
                'message': f'Batch procesado: {len(articulos_creados)} artículos creados',
                'created_count': len(articulos_creados),
                'articulos': articulos_creados,
                'errors': errores,
                'error_count': len(errores),
                'processed_total': len(articulos_data)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

def api_estadisticas_completas(request):
    """
    API endpoint que retorna estadísticas completas del sistema.
    Útil para verificación post-creación masiva.
    """
    try:
        # Contar elementos principales
        total_articulos = Articulo.objects.count()
        total_productos = Producto.objects.count()
        total_ubicaciones = UbicacionBodega.objects.count()
        total_bodegas = Bodega.objects.count()
        
        # Estadísticas de capacidad
        from django.db.models import Sum
        capacidad_total = UbicacionBodega.objects.aggregate(
            total=Sum('capacidad_total')
        )['total'] or 0
        
        capacidad_disponible = UbicacionBodega.objects.aggregate(
            disponible=Sum('capacidad_disponible')
        )['disponible'] or 0
        
        capacidad_ocupada = capacidad_total - capacidad_disponible
        porcentaje_ocupacion = (capacidad_ocupada / capacidad_total * 100) if capacidad_total > 0 else 0
        
        # Top 5 productos con más artículos
        from django.db.models import Count
        productos_top = Producto.objects.annotate(
            num_articulos=Count('articulo')
        ).order_by('-num_articulos')[:5]
        
        productos_stats = [
            {
            'nombre': p.nombre,
            'articulos': p.num_articulos  # type: ignore
            } for p in productos_top
        ]
        
        # Distribución por ubicación
        from django.db.models import Max, Min, Avg
        ubicaciones_stats = UbicacionBodega.objects.annotate(
            num_articulos=Count('articulo')
        ).aggregate(
            max_articulos=Max('num_articulos'),
            min_articulos=Min('num_articulos'),
            avg_articulos=Avg('num_articulos')
        )
        
        return JsonResponse({
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'totales': {
                'total_articulos': total_articulos,
                'total_productos': total_productos,
                'total_ubicaciones': total_ubicaciones,
                'total_bodegas': total_bodegas
            },
            'capacidad': {
                'capacidad_total': capacidad_total,
                'capacidad_disponible': capacidad_disponible,
                'capacidad_ocupada': capacidad_ocupada,
                'porcentaje_ocupacion': round(porcentaje_ocupacion, 2)
            },
            'productos_top': productos_stats,
            'distribucion': {
                'max_articulos_por_ubicacion': ubicaciones_stats['max_articulos'] or 0,
                'min_articulos_por_ubicacion': ubicaciones_stats['min_articulos'] or 0,
                'promedio_articulos_por_ubicacion': round(ubicaciones_stats['avg_articulos'] or 0, 2)
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =========================
# ENDPOINTS DE ELIMINACION MASIVA
# =========================

@require_roles('admin')
@jwt_required
def eliminar_todos_articulos(request):
    """
    Endpoint para eliminar todos los artículos del sistema.
    Útil para limpiar datos de prueba.
    """
    if request.method == 'DELETE':
        try:
            # Contar artículos antes de eliminar
            total_articulos = Articulo.objects.count()
            
            if total_articulos == 0:
                return JsonResponse({
                    'success': True,
                    'message': 'No hay artículos para eliminar',
                    'eliminados': 0
                })
            
            # Liberar capacidad en ubicaciones antes de eliminar
            ubicaciones_afectadas = {}
            for articulo in Articulo.objects.all():
                ubicacion_id = articulo.ubicacion.pk
                if ubicacion_id not in ubicaciones_afectadas:
                    ubicaciones_afectadas[ubicacion_id] = 0
                ubicaciones_afectadas[ubicacion_id] += 1
            
            # Actualizar capacidad disponible en ubicaciones
            for ubicacion_id, cantidad in ubicaciones_afectadas.items():
                ubicacion = UbicacionBodega.objects.get(id=ubicacion_id)
                ubicacion.capacidad_disponible += cantidad
                ubicacion.save()
            
            # Eliminar todos los artículos
            Articulo.objects.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Eliminados {total_articulos} artículos exitosamente',
                'eliminados': total_articulos,
                'ubicaciones_liberadas': len(ubicaciones_afectadas)
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error eliminando artículos: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'error': 'Método no permitido. Use DELETE'
        }, status=405)

def eliminar_todas_ubicaciones(request):
    """
    Endpoint para eliminar todas las ubicaciones de bodega.
    PRECONDICION: No deben existir artículos.
    """
    if request.method == 'DELETE':
        try:
            # Verificar que no haya artículos
            total_articulos = Articulo.objects.count()
            if total_articulos > 0:
                return JsonResponse({
                    'error': f'No se pueden eliminar ubicaciones. Existen {total_articulos} artículos. Elimínelos primero.'
                }, status=400)
            
            # Contar ubicaciones antes de eliminar
            total_ubicaciones = UbicacionBodega.objects.count()
            
            if total_ubicaciones == 0:
                return JsonResponse({
                    'success': True,
                    'message': 'No hay ubicaciones para eliminar',
                    'eliminados': 0
                })
            
            # Eliminar todas las ubicaciones
            UbicacionBodega.objects.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Eliminadas {total_ubicaciones} ubicaciones exitosamente',
                'eliminados': total_ubicaciones
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error eliminando ubicaciones: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'error': 'Método no permitido. Use DELETE'
        }, status=405)

def eliminar_todas_bodegas(request):
    """
    Endpoint para eliminar todas las bodegas.
    PRECONDICION: No deben existir ubicaciones.
    """
    if request.method == 'DELETE':
        try:
            # Verificar que no haya ubicaciones
            total_ubicaciones = UbicacionBodega.objects.count()
            if total_ubicaciones > 0:
                return JsonResponse({
                    'error': f'No se pueden eliminar bodegas. Existen {total_ubicaciones} ubicaciones. Elimínelas primero.'
                }, status=400)
            
            # Contar bodegas antes de eliminar
            total_bodegas = Bodega.objects.count()
            
            if total_bodegas == 0:
                return JsonResponse({
                    'success': True,
                    'message': 'No hay bodegas para eliminar',
                    'eliminados': 0
                })
            
            # Eliminar todas las bodegas
            Bodega.objects.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Eliminadas {total_bodegas} bodegas exitosamente',
                'eliminados': total_bodegas
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error eliminando bodegas: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'error': 'Método no permitido. Use DELETE'
        }, status=405)

@require_roles('admin')
@jwt_required
def eliminar_todos_productos(request):
    """
    Endpoint para eliminar todos los productos.
    PRECONDICION: No deben existir artículos asociados.
    """
    if request.method == 'DELETE':
        try:
            # Verificar que no haya artículos
            total_articulos = Articulo.objects.count()
            if total_articulos > 0:
                return JsonResponse({
                    'error': f'No se pueden eliminar productos. Existen {total_articulos} artículos asociados. Elimínelos primero.'
                }, status=400)
            
            # Contar productos antes de eliminar
            total_productos = Producto.objects.count()
            
            if total_productos == 0:
                return JsonResponse({
                    'success': True,
                    'message': 'No hay productos para eliminar',
                    'eliminados': 0
                })
            
            # Eliminar todos los productos
            Producto.objects.all().delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Eliminados {total_productos} productos exitosamente',
                'eliminados': total_productos
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error eliminando productos: {str(e)}'
            }, status=500)
    else:
        return JsonResponse({
            'error': 'Método no permitido. Use DELETE'
        }, status=405)

