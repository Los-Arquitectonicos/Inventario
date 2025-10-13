"""
Script para crear datos de prueba para el sistema de pedidos.
Ejecutar con: python manage.py shell < tests/create_orders_test_data.py
"""

from django.contrib.auth.models import User
from inventario.models import Producto, Articulo, Bodega, ZonaBodega, Categoria, Proveedor, Pedido, DetallePedido
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import uuid

print("🚀 Iniciando creación de datos de prueba para pedidos...")

# Crear usuarios si no existen
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@inventario.com',
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    user.set_password('admin123')
    user.save()
    print(f"✅ Usuario administrador creado: {user.username}")
else:
    print(f"ℹ️  Usuario administrador ya existe: {user.username}")

# Crear usuario operador
operator, created = User.objects.get_or_create(
    username='operador',
    defaults={
        'email': 'operador@inventario.com',
        'first_name': 'Juan',
        'last_name': 'Operador',
        'is_staff': False,
        'is_superuser': False
    }
)
if created:
    operator.set_password('op123456')
    operator.save()
    print(f"✅ Usuario operador creado: {operator.username}")
else:
    print(f"ℹ️  Usuario operador ya existe: {operator.username}")

# Crear categoría si no existe
categoria, created = Categoria.objects.get_or_create(
    nombre='Electrónicos',
    defaults={'descripcion': 'Dispositivos y componentes electrónicos'}
)
if created:
    print(f"✅ Categoría creada: {categoria.nombre}")

# Crear proveedor si no existe
proveedor, created = Proveedor.objects.get_or_create(
    nombre='TechSupply',
    defaults={
        'email': 'contacto@techsupply.com',
        'telefono': '+1234567890',
        'direccion': 'Av. Principal 123, Ciudad Tech'
    }
)
if created:
    print(f"✅ Proveedor creado: {proveedor.nombre}")

# Crear bodegas
bodega_principal, created = Bodega.objects.get_or_create(
    codigo='BOD-001',
    defaults={
        'nombre': 'Bodega Principal',
        'direccion': 'Calle Industrial 123',
        'ciudad': 'Ciudad Principal',
        'telefono': '+1234567891',
        'capacidad_maxima': 1000,
        'responsable': user
    }
)
if created:
    print(f"✅ Bodega creada: {bodega_principal.nombre}")

bodega_secundaria, created = Bodega.objects.get_or_create(
    codigo='BOD-002',
    defaults={
        'nombre': 'Bodega Secundaria',
        'direccion': 'Avenida Comercial 456',
        'ciudad': 'Ciudad Norte',
        'telefono': '+1234567892',
        'capacidad_maxima': 500,
        'responsable': operator
    }
)
if created:
    print(f"✅ Bodega creada: {bodega_secundaria.nombre}")

# Crear zonas de bodega
zona_a, created = ZonaBodega.objects.get_or_create(
    bodega=bodega_principal,
    codigo='A-01',
    defaults={
        'nombre': 'Zona A',
        'descripcion': 'Productos de alta rotación'
    }
)

zona_b, created = ZonaBodega.objects.get_or_create(
    bodega=bodega_principal,
    codigo='B-01',
    defaults={
        'nombre': 'Zona B', 
        'descripcion': 'Productos especiales'
    }
)

zona_c, created = ZonaBodega.objects.get_or_create(
    bodega=bodega_secundaria,
    codigo='C-01',
    defaults={
        'nombre': 'Zona C',
        'descripcion': 'Almacén general'
    }
)

# Crear productos si no existen
productos_data = [
    {
        'sku': 'LAPTOP-001',
        'nombre': 'Laptop HP EliteBook',
        'descripcion': 'Laptop profesional HP EliteBook 14"',
        'precio_costo': Decimal('800.00'),
        'precio_venta': Decimal('1200.00'),
        'stock_minimo': 5
    },
    {
        'sku': 'MOUSE-001',
        'nombre': 'Mouse Inalámbrico Logitech',
        'descripcion': 'Mouse inalámbrico con sensor óptico',
        'precio_costo': Decimal('15.00'),
        'precio_venta': Decimal('25.00'),
        'stock_minimo': 20
    },
    {
        'sku': 'MONITOR-001',
        'nombre': 'Monitor Samsung 24"',
        'descripcion': 'Monitor LED 24 pulgadas Full HD',
        'precio_costo': Decimal('150.00'),
        'precio_venta': Decimal('250.00'),
        'stock_minimo': 10
    },
    {
        'sku': 'TECLADO-001',
        'nombre': 'Teclado Mecánico RGB',
        'descripcion': 'Teclado mecánico con retroiluminación RGB',
        'precio_costo': Decimal('60.00'),
        'precio_venta': Decimal('99.99'),
        'stock_minimo': 15
    },
    {
        'sku': 'CABLE-001',
        'nombre': 'Cable HDMI 2.0',
        'descripcion': 'Cable HDMI 2.0 de 2 metros',
        'precio_costo': Decimal('8.00'),
        'precio_venta': Decimal('15.00'),
        'stock_minimo': 50
    }
]

productos_creados = []
for prod_data in productos_data:
    producto, created = Producto.objects.get_or_create(
        sku=prod_data['sku'],
        defaults={
            'nombre': prod_data['nombre'],
            'descripcion': prod_data['descripcion'],
            'categoria': categoria,
            'proveedor': proveedor,
            'precio_costo': prod_data['precio_costo'],
            'precio_venta': prod_data['precio_venta'],
            'stock_minimo': prod_data['stock_minimo']
        }
    )
    productos_creados.append(producto)
    if created:
        print(f"✅ Producto creado: {producto.nombre} ({producto.sku})")

# Crear artículos (inventario físico)
articulos_data = [
    # Laptops - 8 unidades
    {'producto_sku': 'LAPTOP-001', 'bodega': bodega_principal, 'zona': zona_a, 'cantidad': 5},
    {'producto_sku': 'LAPTOP-001', 'bodega': bodega_secundaria, 'zona': zona_c, 'cantidad': 3},
    
    # Mouses - 30 unidades
    {'producto_sku': 'MOUSE-001', 'bodega': bodega_principal, 'zona': zona_a, 'cantidad': 20},
    {'producto_sku': 'MOUSE-001', 'bodega': bodega_secundaria, 'zona': zona_c, 'cantidad': 10},
    
    # Monitores - 15 unidades
    {'producto_sku': 'MONITOR-001', 'bodega': bodega_principal, 'zona': zona_b, 'cantidad': 10},
    {'producto_sku': 'MONITOR-001', 'bodega': bodega_secundaria, 'zona': zona_c, 'cantidad': 5},
    
    # Teclados - 25 unidades
    {'producto_sku': 'TECLADO-001', 'bodega': bodega_principal, 'zona': zona_a, 'cantidad': 15},
    {'producto_sku': 'TECLADO-001', 'bodega': bodega_secundaria, 'zona': zona_c, 'cantidad': 10},
    
    # Cables - 80 unidades
    {'producto_sku': 'CABLE-001', 'bodega': bodega_principal, 'zona': zona_a, 'cantidad': 50},
    {'producto_sku': 'CABLE-001', 'bodega': bodega_secundaria, 'zona': zona_c, 'cantidad': 30},
]

for articulo_data in articulos_data:
    producto = Producto.objects.get(sku=articulo_data['producto_sku'])
    
    # Crear múltiples artículos individuales
    for i in range(articulo_data['cantidad']):
        articulo = Articulo(
            producto=producto,
            bodega=articulo_data['bodega'],
            zona=articulo_data['zona'],
            numero_serie=f"{producto.sku}-{uuid.uuid4().hex[:8].upper()}",
            estado='disponible',
            lote=f"LOTE-{timezone.now().strftime('%Y%m')}-001"
        )
        articulo.save()
        created = True
        if created:
            print(f"✅ Artículo creado: {articulo.numero_serie}")

print("\n📦 Creando pedidos de prueba...")

# Crear pedidos de prueba
pedidos_data = [
    {
        'tipo_pedido': 'venta',
        'estado': 'pendiente',
        'cliente_nombre': 'Empresa ABC S.A.',
        'cliente_email': 'compras@empresaabc.com',
        'cliente_telefono': '+1987654321',
        'direccion_entrega': 'Av. Empresarial 456, Oficina 301',
        'notas': 'Entregar en horario de oficina (8am-5pm)',
        'fecha_requerida': timezone.now() + timedelta(days=5),
        'usuario_asignado': operator,
        'detalles': [
            {'sku': 'LAPTOP-001', 'cantidad': 2, 'precio': Decimal('1150.00')},
            {'sku': 'MOUSE-001', 'cantidad': 2, 'precio': Decimal('23.00')},
            {'sku': 'MONITOR-001', 'cantidad': 2, 'precio': Decimal('240.00')},
        ]
    },
    {
        'tipo_pedido': 'venta',
        'estado': 'preparando',
        'cliente_nombre': 'TechStart Ltda.',
        'cliente_email': 'admin@techstart.com',
        'cliente_telefono': '+1555666777',
        'direccion_entrega': 'Calle Nueva 789, Piso 2',
        'notas': 'Cliente frecuente - descuento aplicado',
        'observaciones_internas': 'Cliente VIP con descuento del 5%',
        'fecha_requerida': timezone.now() + timedelta(days=3),
        'usuario_asignado': user,
        'detalles': [
            {'sku': 'TECLADO-001', 'cantidad': 5, 'precio': Decimal('95.00')},
            {'sku': 'MOUSE-001', 'cantidad': 5, 'precio': Decimal('24.00')},
            {'sku': 'CABLE-001', 'cantidad': 10, 'precio': Decimal('14.00')},
        ]
    },
    {
        'tipo_pedido': 'transferencia',
        'estado': 'listo',
        'cliente_nombre': 'Sucursal Norte',
        'direccion_entrega': 'Bodega Sucursal Norte - Zona Industrial',
        'notas': 'Transferencia interna para restock',
        'observaciones_internas': 'Transferir de bodega principal a secundaria',
        'fecha_requerida': timezone.now() + timedelta(days=1),
        'usuario_asignado': operator,
        'detalles': [
            {'sku': 'MONITOR-001', 'cantidad': 3, 'precio': Decimal('150.00')},  # Precio de costo para transferencia
            {'sku': 'CABLE-001', 'cantidad': 20, 'precio': Decimal('8.00')},
        ]
    },
    {
        'tipo_pedido': 'venta',
        'estado': 'pendiente',
        'cliente_nombre': 'Freelancer Solutions',
        'cliente_email': 'pedro@freelancer.com',
        'cliente_telefono': '+1444555666',
        'direccion_entrega': 'Residencial Los Pinos, Casa 25',
        'notas': 'Llamar antes de entregar',
        'fecha_requerida': timezone.now() + timedelta(days=7),
        'detalles': [
            {'sku': 'LAPTOP-001', 'cantidad': 1, 'precio': Decimal('1200.00')},
            {'sku': 'MOUSE-001', 'cantidad': 1, 'precio': Decimal('25.00')},
            {'sku': 'TECLADO-001', 'cantidad': 1, 'precio': Decimal('99.99')},
        ]
    },
    {
        'tipo_pedido': 'venta',
        'estado': 'pendiente',
        'cliente_nombre': 'Gaming Center XYZ',
        'cliente_email': 'info@gamingcenter.com',
        'cliente_telefono': '+1333444555',
        'direccion_entrega': 'Centro Comercial Plaza, Local 15',
        'notas': 'Entrega urgente para evento especial',
        'fecha_requerida': timezone.now() + timedelta(days=2),
        'usuario_asignado': user,
        'detalles': [
            {'sku': 'MONITOR-001', 'cantidad': 4, 'precio': Decimal('245.00')},
            {'sku': 'TECLADO-001', 'cantidad': 4, 'precio': Decimal('97.00')},
            {'sku': 'MOUSE-001', 'cantidad': 4, 'precio': Decimal('24.50')},
            {'sku': 'CABLE-001', 'cantidad': 8, 'precio': Decimal('14.50')},
        ]
    }
]

pedidos_creados = []
for pedido_data in pedidos_data:
    # Crear el pedido
    pedido = Pedido(
        tipo_pedido=pedido_data['tipo_pedido'],
        estado=pedido_data['estado'],
        cliente_nombre=pedido_data['cliente_nombre'],
        cliente_email=pedido_data.get('cliente_email'),
        cliente_telefono=pedido_data.get('cliente_telefono'),
        direccion_entrega=pedido_data['direccion_entrega'],
        notas=pedido_data.get('notas'),
        observaciones_internas=pedido_data.get('observaciones_internas'),
        fecha_requerida=pedido_data['fecha_requerida'],
        usuario_creador=user,
        usuario_asignado=pedido_data.get('usuario_asignado')
    )
    pedido.save()
    
    # Agregar detalles
    for detalle_data in pedido_data['detalles']:
        producto = Producto.objects.get(sku=detalle_data['sku'])
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=detalle_data['cantidad'],
            precio_unitario=detalle_data['precio']
        )
    
    pedidos_creados.append(pedido)
    print(f"✅ Pedido creado: {pedido.numero_pedido} - {pedido.cliente_nombre}")

print(f"\n🎉 ¡Datos de prueba creados exitosamente!")
print(f"👥 Usuarios: {User.objects.count()}")
print(f"📦 Productos: {Producto.objects.count()}")
print(f"📋 Artículos: {Articulo.objects.count()}")
print(f"🏪 Bodegas: {Bodega.objects.count()}")
print(f"📝 Pedidos: {Pedido.objects.count()}")
print(f"🔢 Detalles de pedidos: {DetallePedido.objects.count()}")

print(f"\n📊 Resumen de pedidos creados:")
for pedido in pedidos_creados:
    print(f"  • {pedido.numero_pedido}: {pedido.estado} - {pedido.cliente_nombre} (${pedido.valor_total})")
    ubicaciones = pedido.obtener_ubicaciones_productos()
    disponible = all(u['completamente_disponible'] for u in ubicaciones)
    print(f"    Stock disponible: {'✅ SÍ' if disponible else '⚠️ PARCIAL'}")

print(f"\n🔧 Para probar el sistema:")
print(f"1. GET /api/pedidos/ - Listar todos los pedidos")
print(f"2. GET /api/pedidos/1/ - Ver detalles del primer pedido")  
print(f"3. GET /api/pedidos/1/ubicaciones/ - Ver ubicaciones de productos del pedido")
print(f"4. POST /api/pedidos/1/estado/ con {{'nuevo_estado': 'preparando'}} - Cambiar estado")
print(f"5. POST /api/pedidos/crear/ - Crear nuevo pedido")