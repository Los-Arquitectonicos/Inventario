#!/usr/bin/env python
"""
Comprehensive test of all inventory API endpoints
"""
import os
import sys
import django
from django.test import RequestFactory
import json

# Add the project directory to the Python path
sys.path.append('/Users/pedropablosanintrujillo/GitHub/Inventario')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario.settings')
django.setup()

from inventario.views import productos, bodegas, articulos, movimientos
from inventario.models import Producto, Bodega, Articulo, MovimientoArticulo

def test_all_endpoints():
    """Comprehensive test of all API endpoints"""
    factory = RequestFactory()
    
    print("🚀 COMPREHENSIVE INVENTORY API TEST")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Get all products
    print("\n1. Testing GET /api/productos/")
    total_tests += 1
    try:
        request = factory.get('/api/productos/')
        response = productos.productos_list(request)
        data = json.loads(response.content)
        
        if response.status_code == 200 and 'productos' in data:
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Products found: {len(data['productos'])}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get specific product
    print("\n2. Testing GET /api/productos/1/")
    total_tests += 1
    try:
        request = factory.get('/api/productos/1/')
        response = productos.producto_detail(request, 1)
        data = json.loads(response.content)
        
        if response.status_code == 200 and 'nombre' in data:
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Product: {data['nombre']}")
            print(f"✅ Stock: {data['cantidad_total']}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get all warehouses
    print("\n3. Testing GET /api/bodegas/")
    total_tests += 1
    try:
        request = factory.get('/api/bodegas/')
        response = bodegas.bodegas_list(request)
        data = json.loads(response.content)
        
        if response.status_code == 200 and 'bodegas' in data:
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Warehouses found: {len(data['bodegas'])}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get warehouse inventory
    print("\n4. Testing GET /api/bodegas/1/inventario/")
    total_tests += 1
    try:
        request = factory.get('/api/bodegas/1/inventario/')
        response = bodegas.bodega_inventario(request, 1)
        data = json.loads(response.content)
        
        if response.status_code == 200 and 'inventario' in data:
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Warehouse: {data['bodega']}")
            print(f"✅ Products in inventory: {len(data['inventario'])}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Get articles for a product
    print("\n5. Testing GET /api/productos/1/articulos/")
    total_tests += 1
    try:
        request = factory.get('/api/productos/1/articulos/')
        response = productos.producto_articulos(request, 1)
        data = json.loads(response.content)
        
        if response.status_code == 200 and 'articulos' in data:
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Articles found: {len(data['articulos'])}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Create a new product
    print("\n6. Testing POST /api/productos/crear/")
    total_tests += 1
    try:
        product_data = {
            "nombre": "Test Product New",
            "sku": f"TEST-NEW-{total_tests}",
            "precio_costo": 25.00,
            "precio_venta": 45.00,
            "descripcion": "New test product via API",
            "stock_minimo": 3,
            "stock_maximo": 50
        }
        request = factory.post('/api/productos/crear/', 
                              data=json.dumps(product_data),
                              content_type='application/json')
        response = productos.crear_producto(request)
        data = json.loads(response.content)
        
        if response.status_code == 200 and data.get('success'):
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Message: {data['message']}")
            print(f"✅ New product ID: {data['producto_id']}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Response: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Add new article
    print("\n7. Testing POST /api/articulos/agregar/")
    total_tests += 1
    try:
        article_data = {
            "producto_id": 1,
            "bodega_id": 1,
            "numero_serie": f"TEST{total_tests}456",
            "codigo_barras": f"98765432100{total_tests}"
        }
        request = factory.post('/api/articulos/agregar/',
                              data=json.dumps(article_data),
                              content_type='application/json')
        response = articulos.agregar_articulo(request)
        data = json.loads(response.content)
        
        if response.status_code == 200 and data.get('success'):
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Message: {data['message']}")
            print(f"✅ Article ID: {data['articulo_id']}")
            print(f"✅ Internal code: {data['codigo_interno']}")
            tests_passed += 1
            new_article_id = data['articulo_id']
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Response: {data}")
            new_article_id = 1  # fallback
    except Exception as e:
        print(f"❌ Error: {e}")
        new_article_id = 1  # fallback
    
    # Test 8: Update article status
    print(f"\n8. Testing PUT /api/articulos/{new_article_id}/estado/")
    total_tests += 1
    try:
        update_data = {
            "estado": "reservado",
            "motivo": "Reservado para test automatizado"
        }
        request = factory.put(f'/api/articulos/{new_article_id}/estado/',
                             data=json.dumps(update_data),
                             content_type='application/json')
        response = articulos.actualizar_articulo_estado(request, new_article_id)
        data = json.loads(response.content)
        
        if response.status_code == 200 and data.get('success'):
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Message: {data['message']}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Response: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 9: Get article movements
    print(f"\n9. Testing GET /api/articulos/{new_article_id}/movimientos/")
    total_tests += 1
    try:
        request = factory.get(f'/api/articulos/{new_article_id}/movimientos/')
        response = movimientos.movimientos_articulo(request, new_article_id)
        data = json.loads(response.content)
        
        if response.status_code == 200 and 'movimientos' in data:
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Movements found: {len(data['movimientos'])}")
            if data['movimientos']:
                latest = data['movimientos'][0]
                print(f"✅ Latest movement: {latest['tipo_movimiento']}")
            tests_passed += 1
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Database summary
    print("\n" + "=" * 60)
    print("📊 CURRENT DATABASE STATE")
    print("=" * 60)
    print(f"Products: {Producto.objects.count()}")
    print(f"Warehouses: {Bodega.objects.count()}")
    print(f"Total Articles: {Articulo.objects.count()}")
    print(f"Available Articles: {Articulo.objects.filter(estado='disponible').count()}")
    print(f"Reserved Articles: {Articulo.objects.filter(estado='reservado').count()}")
    print(f"Sold Articles: {Articulo.objects.filter(estado='vendido').count()}")
    print(f"Movement Records: {MovimientoArticulo.objects.count()}")
    
    # Test summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    print(f"❌ Tests failed: {total_tests - tests_passed}/{total_tests}")
    print(f"📈 Success rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your inventory API is working perfectly!")
    else:
        print(f"\n⚠️ {total_tests - tests_passed} test(s) failed. Check the implementation.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    test_all_endpoints()