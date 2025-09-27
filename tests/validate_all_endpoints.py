#!/usr/bin/env python3
"""
Validación completa de endpoints de pedidos para verificar que JMeter funcionará correctamente.
Simula exactamente los requests que hace el test JMeter.
"""

import requests
import json
import sys
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"

def log(message):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def validate_json_response(response, endpoint_name):
    """Valida que la respuesta sea JSON válido"""
    try:
        json_data = response.json()
        log(f"✅ {endpoint_name}: JSON válido")
        return json_data
    except json.JSONDecodeError as e:
        log(f"❌ {endpoint_name}: Error JSON - {e}")
        log(f"   Contenido recibido: {response.text[:200]}...")
        return None

def test_pedidos_list():
    """Test 1: Lista de pedidos (Simula JMeter Test 1)"""
    log("🧪 Test 1: GET /api/pedidos/ - Lista de pedidos")
    
    try:
        response = requests.get(f"{BASE_URL}/api/pedidos/", timeout=10)
        log(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            log(f"❌ Error HTTP: {response.status_code}")
            return False
            
        data = validate_json_response(response, "Lista pedidos")
        if not data:
            return False
            
        # Verificar estructura (igual que las aserciones JMeter)
        if 'success' not in data or not data['success']:
            log("❌ Campo 'success' faltante o false")
            return False
            
        if 'pedidos' not in data:
            log("❌ Campo 'pedidos' faltante")
            return False
            
        if not isinstance(data['pedidos'], list):
            log("❌ 'pedidos' no es una lista")
            return False
            
        if len(data['pedidos']) == 0:
            log("⚠️  Lista de pedidos vacía")
        else:
            log(f"✅ Lista contiene {len(data['pedidos'])} pedidos")
            
        return True
        
    except requests.exceptions.RequestException as e:
        log(f"❌ Error de conexión: {e}")
        return False

def test_pedido_individual(pedido_id=1):
    """Test 2: Pedido individual (Simula JMeter Test 2)"""
    log(f"🧪 Test 2: GET /api/pedidos/{pedido_id}/ - Pedido individual")
    
    try:
        response = requests.get(f"{BASE_URL}/api/pedidos/{pedido_id}/", timeout=10)
        log(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            log(f"❌ Error HTTP: {response.status_code}")
            return False
            
        data = validate_json_response(response, f"Pedido {pedido_id}")
        if not data:
            return False
            
        # Verificar estructura (igual que las aserciones JMeter)
        if 'success' not in data or not data['success']:
            log("❌ Campo 'success' faltante o false")
            return False
            
        if 'pedido' not in data:
            log("❌ Campo 'pedido' faltante")
            return False
            
        pedido = data['pedido']
        if 'id' not in pedido:
            log("❌ Campo 'pedido.id' faltante")
            return False
            
        log(f"✅ Pedido {pedido['id']}: {pedido.get('numero_pedido', 'SIN_NUMERO')}")
        return True
        
    except requests.exceptions.RequestException as e:
        log(f"❌ Error de conexión: {e}")
        return False

def test_ubicaciones_productos(pedido_id=1):
    """Test 3: Ubicaciones productos (Simula JMeter Test 3 - FUNCIÓN PRINCIPAL)"""
    log(f"🧪 Test 3: GET /api/pedidos/{pedido_id}/ubicaciones/ - Ubicaciones productos (PRINCIPAL)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/pedidos/{pedido_id}/ubicaciones/", timeout=15)
        log(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            log(f"❌ Error HTTP: {response.status_code}")
            return False
            
        data = validate_json_response(response, f"Ubicaciones pedido {pedido_id}")
        if not data:
            return False
            
        # Verificar estructura (igual que las aserciones JMeter)
        if 'success' not in data or not data['success']:
            log("❌ Campo 'success' faltante o false")
            return False
            
        if 'pedido_id' not in data:
            log("❌ Campo 'pedido_id' faltante")
            return False
            
        if 'ubicaciones_productos' not in data:
            log("❌ Campo 'ubicaciones_productos' faltante")
            return False
            
        ubicaciones = data['ubicaciones_productos']
        if not isinstance(ubicaciones, list):
            log("❌ 'ubicaciones_productos' no es una lista")
            return False
            
        log(f"✅ Ubicaciones para {len(ubicaciones)} productos")
        
        # Verificar estructura detallada del primer producto si existe
        if len(ubicaciones) > 0:
            primer_producto = ubicaciones[0]
            campos_requeridos = ['producto_id', 'producto_nombre', 'cantidad_pedida', 'ubicaciones']
            for campo in campos_requeridos:
                if campo not in primer_producto:
                    log(f"⚠️  Campo '{campo}' faltante en producto")
                else:
                    log(f"✅ Campo '{campo}' presente")
        
        return True
        
    except requests.exceptions.RequestException as e:
        log(f"❌ Error de conexión: {e}")
        return False

def main():
    """Ejecuta todos los tests que simulan JMeter"""
    log("🚀 Iniciando validación de endpoints para compatibilidad JMeter")
    log(f"   Base URL: {BASE_URL}")
    
    # Verificar conectividad básica
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        log("✅ Servidor Django accesible")
    except:
        log("❌ No se puede conectar al servidor Django")
        log("   Asegúrate de que Django esté ejecutándose en puerto 8001")
        return False
    
    # Ejecutar tests secuencialmente
    tests = [
        ("Lista de pedidos", test_pedidos_list),
        ("Pedido individual", lambda: test_pedido_individual(1)),
        ("Ubicaciones productos", lambda: test_ubicaciones_productos(1))
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        log(f"\n{'='*50}")
        resultado = test_func()
        resultados.append((nombre, resultado))
        
        if resultado:
            log(f"✅ {nombre}: PASSED")
        else:
            log(f"❌ {nombre}: FAILED")
        
        # Pausa entre tests (simula JMeter timer)
        time.sleep(0.8)
    
    # Resumen final
    log(f"\n{'='*50}")
    log("📊 RESUMEN DE RESULTADOS")
    log(f"{'='*50}")
    
    passed = sum(1 for _, result in resultados if result)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        log(f"   {nombre}: {status}")
    
    log(f"\n🎯 Total: {passed}/{total} tests pasaron")
    
    if passed == total:
        log("🎉 ¡TODOS LOS TESTS PASARON! JMeter debería funcionar correctamente.")
        return True
    else:
        log("⚠️  Hay tests fallando. Revisar errores antes de ejecutar JMeter.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)