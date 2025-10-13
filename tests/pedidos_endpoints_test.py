#!/usr/bin/env python3
"""
Test manual para verificar que los endpoints de pedidos funcionan correctamente
antes de ejecutar JMeter.
"""
import requests
import json
import time
import sys

def test_endpoint(url, expected_fields=None):
    """Probar un endpoint y verificar que devuelve JSON válido"""
    try:
        print(f"🔍 Probando: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ JSON válido")
                
                if expected_fields:
                    for field in expected_fields:
                        if field in data:
                            print(f"   ✅ Campo '{field}' presente")
                        else:
                            print(f"   ❌ Campo '{field}' faltante")
                            return False
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Error JSON: {e}")
                print(f"   Response: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ Status code incorrecto: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.RequestException as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def main():
    base_url = "http://127.0.0.1:8001"
    
    print("🚀 Test de Endpoints de Pedidos")
    print("=" * 50)
    
    # Test de endpoints
    tests = [
        {
            "url": f"{base_url}/api/pedidos/",
            "expected_fields": ["pedidos", "success"],
            "description": "Lista de pedidos"
        },
        {
            "url": f"{base_url}/api/pedidos/1/",
            "expected_fields": ["success", "pedido"],
            "description": "Pedido específico"
        },
        {
            "url": f"{base_url}/api/pedidos/1/ubicaciones/",
            "expected_fields": ["success", "pedido_id", "ubicaciones_productos"],
            "description": "Ubicaciones de productos (función principal)"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n📋 {test['description']}")
        success = test_endpoint(test["url"], test["expected_fields"])
        results.append(success)
        
        if success:
            print("   🎉 Test EXITOSO")
        else:
            print("   💥 Test FALLÓ")
        
        time.sleep(0.5)  # Pequeña pausa entre tests
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS")
    print("=" * 50)
    
    successful = sum(results)
    total = len(results)
    
    for i, test in enumerate(tests):
        status = "✅" if results[i] else "❌"
        print(f"{status} {test['description']}")
    
    print(f"\n🎯 Total: {successful}/{total} tests exitosos")
    
    if successful == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ Los endpoints están listos para JMeter")
        print("\n💡 Para ejecutar JMeter:")
        print("   ./tests/run_pedidos_test.sh")
        return 0
    else:
        print("❌ Algunos tests fallaron")
        print("🔧 Revisa los errores antes de ejecutar JMeter")
        return 1

if __name__ == "__main__":
    sys.exit(main())