#!/usr/bin/env python3
"""
Test simple para verificar qué está recibiendo JMeter exactamente
"""

import requests
import json

def test_endpoint_response():
    """Verifica la respuesta exacta del endpoint"""
    
    print("🧪 Verificando respuesta exacta del endpoint /api/pedidos/")
    
    try:
        response = requests.get("http://127.0.0.1:8001/api/pedidos/", timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Content-Type: {response.headers.get('content-type', 'NO CONTENT-TYPE')}")
        print(f"📊 Content-Length: {len(response.text)} caracteres")
        
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"❌ Contenido: {response.text[:500]}...")
            return False
        
        # Intentar parsear JSON
        try:
            data = response.json()
            print(f"✅ JSON válido parseado")
            
            # Verificar estructura específica
            print(f"\n📋 Análisis de estructura JSON:")
            
            # Verificar keys principales
            root_keys = list(data.keys()) if isinstance(data, dict) else []
            print(f"   Keys en raíz: {root_keys}")
            
            # Verificar específicamente el campo 'pedidos'
            has_pedidos = 'pedidos' in data
            print(f"   Campo 'pedidos' existe: {has_pedidos}")
            
            if has_pedidos:
                pedidos = data['pedidos']
                print(f"   Tipo de 'pedidos': {type(pedidos)}")
                print(f"   Es lista: {isinstance(pedidos, list)}")
                
                if isinstance(pedidos, list):
                    print(f"   Número de elementos: {len(pedidos)}")
                    
                    if len(pedidos) > 0:
                        print(f"   Primer elemento es dict: {isinstance(pedidos[0], dict)}")
                        if isinstance(pedidos[0], dict):
                            print(f"   Keys del primer pedido: {list(pedidos[0].keys())[:5]}...")
                            print(f"   ID del primer pedido: {pedidos[0].get('id', 'NO ID')}")
            
            # Test específico para simular JSONPath $['pedidos']
            try:
                result = data['pedidos']
                print(f"\n✅ Acceso data['pedidos']: EXITOSO")
                print(f"   Resultado: {type(result)} con {len(result) if isinstance(result, list) else 0} elementos")
            except KeyError:
                print(f"\n❌ Acceso data['pedidos']: FALLÓ - Key no existe")
            except Exception as e:
                print(f"\n❌ Acceso data['pedidos']: ERROR - {e}")
            
            # Test específico para primer elemento
            try:
                if isinstance(data.get('pedidos'), list) and len(data['pedidos']) > 0:
                    result = data['pedidos'][0]
                    print(f"✅ Acceso data['pedidos'][0]: EXITOSO")
                    print(f"   ID: {result.get('id', 'NO ID')}")
                else:
                    print(f"❌ data['pedidos'][0]: Lista vacía o no existe")
            except Exception as e:
                print(f"❌ Acceso data['pedidos'][0]: ERROR - {e}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"❌ Contenido raw (primeros 500 chars): {response.text[:500]}...")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_with_headers():
    """Test con headers específicos que podría usar JMeter"""
    
    print(f"\n🧪 Test con headers específicos (simulando JMeter)")
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Apache-HttpClient/4.5.14 (Java/11.0.19)',  # Similar a JMeter
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get("http://127.0.0.1:8001/api/pedidos/", headers=headers, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            has_pedidos = 'pedidos' in data
            print(f"✅ Con headers específicos - Campo 'pedidos' existe: {has_pedidos}")
            if has_pedidos:
                print(f"   Número de pedidos: {len(data['pedidos'])}")
        else:
            print(f"❌ Error con headers: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error con headers: {e}")

if __name__ == "__main__":
    success1 = test_endpoint_response()
    test_with_headers()
    
    if success1:
        print(f"\n🎯 CONCLUSIÓN: El endpoint funciona correctamente")
        print(f"   El problema puede estar en:")
        print(f"   1. Configuración de JMeter")
        print(f"   2. URL incorrecta en JMeter")  
        print(f"   3. Headers enviados por JMeter")
        print(f"   4. Sintaxis de JSONPath en JMeter")
    else:
        print(f"\n❌ PROBLEMA: El endpoint no está funcionando correctamente")