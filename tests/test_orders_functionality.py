#!/usr/bin/env python
"""
Script para probar la funcionalidad principal del sistema de pedidos:
Función que retorna productos, cantidades y ubicación en bodega dado un pedido.
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario.settings')
django.setup()

from inventario.models import Pedido, DetallePedido

print('🔍 Probando la función principal del sistema de pedidos...')
print()

# Obtener pedidos disponibles
pedidos = list(Pedido.objects.all())
print(f'📊 Total de pedidos en sistema: {len(pedidos)}')

if pedidos:
    # Probar con el primer pedido
    pedido = pedidos[0]
    print(f'📝 Probando con pedido: {pedido.numero_pedido}')
    print(f'👤 Cliente: {pedido.cliente_nombre}')
    print(f'📊 Estado: {pedido.estado}')
    print(f'💰 Valor total: ${pedido.valor_total}')
    print()
    
    # Esta es la función principal solicitada por el usuario
    print('🏪 FUNCIÓN PRINCIPAL: Obteniendo ubicaciones de productos para el pedido...')
    ubicaciones = pedido.obtener_ubicaciones_productos()
    
    print(f'📦 Productos en el pedido: {len(ubicaciones)}')
    print('=' * 80)
    
    for i, ubicacion in enumerate(ubicaciones, 1):
        print(f'{i}. PRODUCTO: {ubicacion["producto_nombre"]} (SKU: {ubicacion["producto_sku"]})')
        print(f'   📋 Cantidad pedida: {ubicacion["cantidad_pedida"]} unidades')
        print(f'   ✅ Cantidad disponible: {ubicacion["cantidad_disponible"]} unidades')
        
        if ubicacion["cantidad_faltante"] > 0:
            print(f'   ⚠️  FALTANTE: {ubicacion["cantidad_faltante"]} unidades')
        else:
            print(f'   ✅ STOCK COMPLETO')
            
        print(f'   💵 Precio unitario: ${ubicacion["precio_unitario"]}')
        print(f'   💰 Subtotal: ${ubicacion["subtotal"]}')
        
        print(f'   🏪 UBICACIONES EN BODEGAS:')
        for j, ub in enumerate(ubicacion["ubicaciones"], 1):
            print(f'      {j}. Bodega: {ub["bodega"]} (Código: {ub["codigo_bodega"]})')
            print(f'         📦 Cantidad disponible: {ub["cantidad_disponible"]} unidades')
            print(f'         🆔 Artículos específicos: {len(ub["articulos"])} items')
            
        print(f'   ✅ Disponibilidad completa: {"SÍ" if ubicacion["completamente_disponible"] else "NO"}')
        print('-' * 60)
    
    print()
    print('📊 RESUMEN DEL PEDIDO:')
    print(f'✅ ¿Puede ser procesado completamente? {"SÍ" if pedido.puede_ser_procesado() else "NO"}')
    print(f'💰 Valor total del pedido: ${pedido.valor_total}')
    
    # Probar con otro pedido para mostrar diferentes escenarios
    if len(pedidos) > 1:
        print('\n' + '=' * 80)
        print('🔍 Probando con segundo pedido para mostrar diferentes escenarios...')
        
        pedido2 = pedidos[1]
        print(f'📝 Pedido: {pedido2.numero_pedido} - {pedido2.cliente_nombre}')
        
        ubicaciones2 = pedido2.obtener_ubicaciones_productos()
        productos_completos = sum(1 for u in ubicaciones2 if u["completamente_disponible"])
        productos_parciales = sum(1 for u in ubicaciones2 if not u["completamente_disponible"] and u["cantidad_disponible"] > 0)
        productos_sin_stock = sum(1 for u in ubicaciones2 if u["cantidad_disponible"] == 0)
        
        print(f'📊 Productos con stock completo: {productos_completos}')
        print(f'⚠️  Productos con stock parcial: {productos_parciales}')
        print(f'❌ Productos sin stock: {productos_sin_stock}')
    
    print('\n🎉 ¡Función implementada exitosamente!')
    print('La función obtener_ubicaciones_productos() retorna:')
    print('  • Productos del pedido')
    print('  • Cantidades pedidas vs disponibles')  
    print('  • Ubicaciones específicas en bodegas')
    print('  • Información detallada de artículos')
    
else:
    print('❌ No se encontraron pedidos. Ejecuta create_orders_test_data.py primero.')