#!/usr/bin/env python3
"""
Script para crear clientes de prueba en ProvesiWMS.
Ejecutar desde el directorio ProvesiWMS en la instancia EC2.

Uso:
    source /home/ubuntu/app/Inventario/ProvesiWMS/venv/bin/activate
    cd /home/ubuntu/app/Inventario/ProvesiWMS
    /home/ubuntu/app/Inventario/ProvesiWMS/venv/bin/python crear_clientes.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from inventario.models import Cliente

def crear_clientes():
    """Crea clientes de prueba."""
    
    clientes = [
        {
            "nombre": "Almacenes Éxito",
            "email": "compras@exito.com",
            "telefono": "3001234567",
            "direccion": "Calle 100 # 18-30",
            "ciudad": "Bogotá"
        },
        {
            "nombre": "Carrefour Colombia",
            "email": "pedidos@carrefour.co",
            "telefono": "3009876543",
            "direccion": "Avenida El Dorado # 68-30",
            "ciudad": "Bogotá"
        },
        {
            "nombre": "Jumbo Supermercados",
            "email": "compras@jumbo.com.co",
            "telefono": "3012345678",
            "direccion": "Calle 52 # 43-20",
            "ciudad": "Medellín"
        },
        {
            "nombre": "D1 Colombia",
            "email": "logistica@tiendad1.com",
            "telefono": "3156789012",
            "direccion": "Calle 80 # 69B-70",
            "ciudad": "Bogotá"
        },
        {
            "nombre": "Alkosto",
            "email": "compras@alkosto.com",
            "telefono": "3178901234",
            "direccion": "Autopista Sur # 43-30",
            "ciudad": "Bogotá"
        },
        {
            "nombre": "Makro Colombia",
            "email": "pedidos@makro.co",
            "telefono": "3134567890",
            "direccion": "Calle 13 # 37-35",
            "ciudad": "Cali"
        },
        {
            "nombre": "PriceSmart",
            "email": "ventas@pricesmart.com",
            "telefono": "3145678901",
            "direccion": "Calle 6 # 45-10",
            "ciudad": "Barranquilla"
        },
        {
            "nombre": "La 14",
            "email": "compras@la14.com.co",
            "telefono": "3198765432",
            "direccion": "Carrera 15 # 12-25",
            "ciudad": "Bucaramanga"
        },
        {
            "nombre": "Olímpica",
            "email": "logistica@olimpica.com",
            "telefono": "3187654321",
            "direccion": "Avenida Las Américas # 54-20",
            "ciudad": "Cartagena"
        },
        {
            "nombre": "Surtimax",
            "email": "pedidos@surtimax.com",
            "telefono": "3176543210",
            "direccion": "Calle 30 # 82-50",
            "ciudad": "Pereira"
        }
    ]
    
    print("=" * 60)
    print("PROVESI WMS - Creación de Clientes")
    print("=" * 60)
    print()
    
    creados = 0
    existentes = 0
    
    for cliente_data in clientes:
        nombre = cliente_data["nombre"]
        email = cliente_data["email"]
        
        if Cliente.objects.filter(email=email).exists():
            cliente = Cliente.objects.get(email=email)
            print(f"⚠️  {nombre} ya existe (ID: {cliente.id})")
            existentes += 1
        else:
            cliente = Cliente.objects.create(**cliente_data)
            print(f"✅ {nombre} creado (ID: {cliente.id})")
            creados += 1
    
    print()
    print("=" * 60)
    print(f"Resumen:")
    print(f"  - Clientes creados: {creados}")
    print(f"  - Clientes existentes: {existentes}")
    print(f"  - Total: {Cliente.objects.count()}")
    print("=" * 60)
    print()
    
    # Mostrar todos los clientes
    print("📋 Lista de clientes:")
    for cliente in Cliente.objects.all().order_by('id'):
        print(f"   {cliente.id:3d}. {cliente.nombre:30s} | {cliente.ciudad:15s} | {cliente.email}")
    print()

if __name__ == "__main__":
    try:
        crear_clientes()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
