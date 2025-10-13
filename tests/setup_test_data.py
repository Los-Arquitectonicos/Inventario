#!/usr/bin/env python
"""
Script to create test data for the inventory system
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/pedropablosanintrujillo/GitHub/Inventario')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario.settings')
django.setup()

from inventario.models import Categoria, Proveedor, Bodega, ZonaBodega, Producto, Articulo
from django.contrib.auth.models import User

def create_test_data():
    print("Creating test data...")
    
    # Create categories
    cat_electronica = Categoria.objects.get_or_create(
        nombre="Electrónicos",
        defaults={'descripcion': "Productos electrónicos"}
    )[0]
    
    cat_ropa = Categoria.objects.get_or_create(
        nombre="Ropa",
        defaults={'descripcion': "Productos de vestir"}
    )[0]
    
    # Create suppliers
    proveedor_apple = Proveedor.objects.get_or_create(
        nombre="Apple Inc.",
        defaults={
            'email': "supplier@apple.com",
            'telefono': "+1-408-996-1010",
            'direccion': "1 Apple Park Way, Cupertino, CA"
        }
    )[0]
    
    proveedor_nike = Proveedor.objects.get_or_create(
        nombre="Nike Inc.",
        defaults={
            'email': "supplier@nike.com",
            'telefono': "+1-503-671-6453",
            'direccion': "1 Bowerman Dr, Beaverton, OR"
        }
    )[0]
    
    # Create user for warehouse responsible
    user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            'email': "admin@inventory.com",
            'first_name': "Admin",
            'last_name': "User"
        }
    )
    if created:
        user.set_password("admin123")
        user.save()
    
    # Create warehouses
    bodega_madrid = Bodega.objects.get_or_create(
        codigo="MAD001",
        defaults={
            'nombre': "Bodega Madrid",
            'direccion': "Calle Gran Via 123, Madrid",
            'ciudad': "Madrid",
            'telefono': "+34-91-123-4567",
            'responsable': user,
            'capacidad_maxima': 10000
        }
    )[0]
    
    bodega_barcelona = Bodega.objects.get_or_create(
        codigo="BCN001",
        defaults={
            'nombre': "Bodega Barcelona",
            'direccion': "Passeig de Gracia 456, Barcelona",
            'ciudad': "Barcelona",
            'telefono': "+34-93-123-4567",
            'responsable': user,
            'capacidad_maxima': 8000
        }
    )[0]
    
    # Create warehouse zones
    zona_a_madrid = ZonaBodega.objects.get_or_create(
        bodega=bodega_madrid,
        codigo="A1",
        defaults={
            'nombre': "Zona A - Electrónicos",
            'descripcion': "Zona principal para productos electrónicos"
        }
    )[0]
    
    zona_b_madrid = ZonaBodega.objects.get_or_create(
        bodega=bodega_madrid,
        codigo="B1",
        defaults={
            'nombre': "Zona B - Ropa",
            'descripcion': "Zona para productos textiles"
        }
    )[0]
    
    # Create products
    iphone = Producto.objects.get_or_create(
        sku="APPLE-IP15-BLK-128",
        defaults={
            'nombre': "iPhone 15 Black 128GB",
            'descripcion': "Latest iPhone with 128GB storage in Black",
            'categoria': cat_electronica,
            'proveedor': proveedor_apple,
            'precio_costo': 700.00,
            'precio_venta': 999.00,
            'peso': 0.171,
            'dimensiones': "147.6 x 71.6 x 7.80 mm",
            'color': "Black",
            'marca': "Apple",
            'stock_minimo': 5,
            'stock_maximo': 100,
            'requiere_numero_serie': True,
            'es_serializado': True
        }
    )[0]
    
    macbook = Producto.objects.get_or_create(
        sku="APPLE-MBP-M3-16",
        defaults={
            'nombre': "MacBook Pro M3 16-inch",
            'descripcion': "MacBook Pro with M3 chip and 16-inch display",
            'categoria': cat_electronica,
            'proveedor': proveedor_apple,
            'precio_costo': 2000.00,
            'precio_venta': 2499.00,
            'peso': 2.16,
            'dimensiones': "355.7 x 248.1 x 16.8 mm",
            'color': "Space Gray",
            'marca': "Apple",
            'stock_minimo': 2,
            'stock_maximo': 20,
            'requiere_numero_serie': True,
            'es_serializado': True
        }
    )[0]
    
    nike_shirt = Producto.objects.get_or_create(
        sku="NIKE-SHIRT-DRI-L",
        defaults={
            'nombre': "Nike Dri-FIT Shirt Large",
            'descripcion': "Nike Dri-FIT performance shirt in Large size",
            'categoria': cat_ropa,
            'proveedor': proveedor_nike,
            'precio_costo': 15.00,
            'precio_venta': 29.99,
            'peso': 0.15,
            'color': "White",
            'talla': "L",
            'marca': "Nike",
            'stock_minimo': 10,
            'stock_maximo': 200,
            'requiere_numero_serie': False,
            'es_serializado': False
        }
    )[0]
    
    # Create articles (individual instances)
    # iPhone articles in Madrid
    for i in range(3):
        Articulo.objects.get_or_create(
            codigo_interno=f"APPLE-IP15-BLK-128-MAD{i+1:03d}",
            defaults={
                'producto': iphone,
                'bodega': bodega_madrid,
                'zona': zona_a_madrid,
                'numero_serie': f"IP15{i+1:06d}",
                'codigo_barras': f"123456789{i+1:03d}",
                'estado': 'disponible'
            }
        )
    
    # iPhone articles in Barcelona
    for i in range(2):
        Articulo.objects.get_or_create(
            codigo_interno=f"APPLE-IP15-BLK-128-BCN{i+1:03d}",
            defaults={
                'producto': iphone,
                'bodega': bodega_barcelona,
                'numero_serie': f"IP15BCN{i+1:04d}",
                'codigo_barras': f"123456780{i+1:03d}",
                'estado': 'disponible'
            }
        )
    
    # MacBook articles
    Articulo.objects.get_or_create(
        codigo_interno="APPLE-MBP-M3-16-MAD001",
        defaults={
            'producto': macbook,
            'bodega': bodega_madrid,
            'zona': zona_a_madrid,
            'numero_serie': "MBP2024001",
            'codigo_barras': "987654321001",
            'estado': 'disponible'
        }
    )
    
    # Nike shirt articles
    for i in range(15):
        Articulo.objects.get_or_create(
            codigo_interno=f"NIKE-SHIRT-DRI-L-MAD{i+1:03d}",
            defaults={
                'producto': nike_shirt,
                'bodega': bodega_madrid,
                'zona': zona_b_madrid,
                'lote': "LOT2024001",
                'estado': 'disponible'
            }
        )
    
    print("✅ Test data created successfully!")
    print(f"Categories: {Categoria.objects.count()}")
    print(f"Suppliers: {Proveedor.objects.count()}")
    print(f"Warehouses: {Bodega.objects.count()}")
    print(f"Products: {Producto.objects.count()}")
    print(f"Articles: {Articulo.objects.count()}")

if __name__ == "__main__":
    create_test_data()