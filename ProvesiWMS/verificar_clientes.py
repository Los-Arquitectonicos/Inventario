#!/usr/bin/env python
"""
Script para verificar los clientes en la base de datos PostgreSQL
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')
django.setup()

from inventario.models import Cliente

def verificar_clientes():
    """Verificar y mostrar todos los clientes en la base de datos"""
    
    print("\n" + "="*70)
    print("VERIFICACIÓN DE CLIENTES EN LA BASE DE DATOS")
    print("="*70 + "\n")
    
    try:
        # Contar total de clientes
        total_clientes = Cliente.objects.count()
        print(f"📊 Total de clientes en la base de datos: {total_clientes}\n")
        
        if total_clientes == 0:
            print("⚠️  No hay clientes en la base de datos")
            print("   Ejecuta crear_clientes.py para crear clientes de prueba\n")
            return
        
        # Listar todos los clientes
        print("📋 Lista de clientes:\n")
        print(f"{'ID':<5} {'Nombre':<30} {'Email':<30} {'Ciudad':<20}")
        print("-" * 85)
        
        for cliente in Cliente.objects.all().order_by('id'):
            print(f"{cliente.id:<5} {cliente.nombre:<30} {cliente.email:<30} {cliente.ciudad:<20}")
        
        print("\n" + "="*70)
        print("✅ Verificación completada")
        print("="*70 + "\n")
        
        # Verificar cliente con ID 1 específicamente (el que usa el test)
        try:
            cliente_1 = Cliente.objects.get(id=1)
            print(f"✅ Cliente ID 1 existe: {cliente_1.nombre} ({cliente_1.email})")
        except Cliente.DoesNotExist:
            print("⚠️  Cliente ID 1 NO existe - Los tests fallarán")
        
        print()
        
    except Exception as e:
        print(f"❌ Error al verificar clientes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_clientes()
