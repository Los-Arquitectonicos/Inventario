#!/usr/bin/env python3
"""
Script de prueba para Lambda Function URL
"""
import requests
import json
from datetime import datetime

# Configuración
FUNCTION_URL = "https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws"

def print_response(title, response):
    """Imprimir respuesta formateada"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2, default=str)}")
    except:
        print(f"Response: {response.text}")
    print()


def test_crear_pedido():
    """Prueba 1: Crear un nuevo pedido"""
    print("\n🧪 TEST 1: Crear pedido")
    
    payload = {
        "cliente_id": 1,
        "productos": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 2, "cantidad": 1}
        ],
        "notas": f"Pedido de prueba - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    response = requests.post(
        f"{FUNCTION_URL}/pedidos",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print_response("Crear Pedido", response)
    
    # Extraer número de pedido para siguientes pruebas
    if response.status_code == 201:
        data = response.json()
        numero_pedido = data.get("pedido", {}).get("numero_pedido")
        return numero_pedido
    return None


def test_listar_pedidos():
    """Prueba 2: Listar todos los pedidos"""
    print("\n🧪 TEST 2: Listar pedidos")
    
    response = requests.get(f"{FUNCTION_URL}/pedidos")
    print_response("Listar Pedidos", response)


def test_listar_con_filtros():
    """Prueba 3: Listar con filtros"""
    print("\n🧪 TEST 3: Listar con filtros")
    
    # Por cliente
    print("📋 Filtrar por cliente_id=1")
    response = requests.get(f"{FUNCTION_URL}/pedidos?cliente_id=1")
    print_response("Filtro por Cliente", response)
    
    # Por estado
    print("📋 Filtrar por estado=pendiente")
    response = requests.get(f"{FUNCTION_URL}/pedidos?estado=pendiente")
    print_response("Filtro por Estado", response)


def test_obtener_pedido(numero_pedido):
    """Prueba 4: Obtener pedido específico"""
    if not numero_pedido:
        print("\n⚠️  SKIPPED: No hay número de pedido")
        return
    
    print(f"\n🧪 TEST 4: Obtener pedido {numero_pedido}")
    
    response = requests.get(f"{FUNCTION_URL}/pedidos/{numero_pedido}")
    print_response(f"Obtener Pedido {numero_pedido}", response)


def test_actualizar_seguimiento(numero_pedido):
    """Prueba 5: Actualizar seguimiento"""
    if not numero_pedido:
        print("\n⚠️  SKIPPED: No hay número de pedido")
        return
    
    print(f"\n🧪 TEST 5: Actualizar seguimiento {numero_pedido}")
    
    # Transición 1: PENDIENTE → CONFIRMADO
    payload = {
        "nuevo_estado": "confirmado",
        "comentario": "Pedido confirmado por ventas"
    }
    
    response = requests.put(
        f"{FUNCTION_URL}/pedidos/{numero_pedido}/seguimiento",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print_response("Actualizar a CONFIRMADO", response)
    
    # Transición 2: CONFIRMADO → EN_PREPARACION
    payload = {
        "nuevo_estado": "en_preparacion",
        "comentario": "Preparando en almacén"
    }
    
    response = requests.put(
        f"{FUNCTION_URL}/pedidos/{numero_pedido}/seguimiento",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print_response("Actualizar a EN_PREPARACION", response)


def test_error_cases():
    """Prueba 6: Casos de error"""
    print("\n🧪 TEST 6: Casos de error")
    
    # Error: Cliente inexistente
    print("❌ Intentar crear pedido con cliente inexistente")
    payload = {
        "cliente_id": 99999,
        "productos": [{"producto_id": 1, "cantidad": 1}]
    }
    response = requests.post(f"{FUNCTION_URL}/pedidos", json=payload)
    print_response("Cliente Inexistente", response)
    
    # Error: Producto inexistente
    print("❌ Intentar crear pedido con producto inexistente")
    payload = {
        "cliente_id": 1,
        "productos": [{"producto_id": 99999, "cantidad": 1}]
    }
    response = requests.post(f"{FUNCTION_URL}/pedidos", json=payload)
    print_response("Producto Inexistente", response)
    
    # Error: Pedido inexistente
    print("❌ Intentar obtener pedido inexistente")
    response = requests.get(f"{FUNCTION_URL}/pedidos/PED-999999")
    print_response("Pedido Inexistente", response)


def main():
    """Ejecutar todas las pruebas"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🧪 PRUEBAS LAMBDA FUNCTION URL - PEDIDOS           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Function URL: {FUNCTION_URL}
""")
    
    try:
        # Prueba 1: Crear pedido
        numero_pedido = test_crear_pedido()
        
        # Prueba 2: Listar pedidos
        test_listar_pedidos()
        
        # Prueba 3: Listar con filtros
        test_listar_con_filtros()
        
        # Prueba 4: Obtener pedido específico
        test_obtener_pedido(numero_pedido)
        
        # Prueba 5: Actualizar seguimiento
        test_actualizar_seguimiento(numero_pedido)
        
        # Prueba 6: Casos de error
        test_error_cases()
        
        print("\n" + "="*60)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al Function URL")
        print("Verifica que la URL sea correcta y que Lambda esté desplegado")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
