#!/usr/bin/env python3
"""
Test simple para simular exactamente lo que hace JMeter con JSONPath
"""

import requests
import json
from jsonpath_ng import parse

def test_jsonpath_assertions():
    """Simula las aserciones JSONPath de JMeter"""
    
    print("🧪 Simulando aserciones JSONPath de JMeter")
    
    # Hacer request al endpoint
    response = requests.get("http://127.0.0.1:8001/api/pedidos/")
    
    if response.status_code != 200:
        print(f"❌ Error HTTP: {response.status_code}")
        return False
    
    try:
        data = response.json()
        print(f"✅ JSON válido recibido")
        
        # Test 1: $.success
        jsonpath_expr = parse('$.success')
        matches = [match.value for match in jsonpath_expr.find(data)]
        print(f"🔍 $.success: {matches}")
        
        # Test 2: $.pedidos (lo que está fallando)
        jsonpath_expr = parse('$.pedidos')
        matches = [match.value for match in jsonpath_expr.find(data)]
        print(f"🔍 $.pedidos: {'Found' if matches else 'NOT FOUND'}")
        if matches:
            print(f"   Tipo: {type(matches[0])}, Longitud: {len(matches[0]) if isinstance(matches[0], list) else 'N/A'}")
        
        # Test 3: $.pedidos[0]
        jsonpath_expr = parse('$.pedidos[0]')
        matches = [match.value for match in jsonpath_expr.find(data)]
        print(f"🔍 $.pedidos[0]: {'Found' if matches else 'NOT FOUND'}")
        if matches:
            print(f"   ID del primer pedido: {matches[0].get('id', 'NO ID')}")
        
        # Test 4: Verificar estructura completa
        print(f"\n📋 Estructura del JSON:")
        print(f"   Keys en raíz: {list(data.keys())}")
        print(f"   'pedidos' existe: {'pedidos' in data}")
        print(f"   Tipo de 'pedidos': {type(data.get('pedidos', 'NO EXISTE'))}")
        
        if 'pedidos' in data and isinstance(data['pedidos'], list):
            print(f"   Número de pedidos: {len(data['pedidos'])}")
            if len(data['pedidos']) > 0:
                print(f"   Keys del primer pedido: {list(data['pedidos'][0].keys())[:5]}...")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    test_jsonpath_assertions()