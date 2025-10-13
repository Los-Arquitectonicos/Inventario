#!/usr/bin/env python3
"""
Script de prueba para endpoints de API de inventario
"""
import requests
import json
import time
import subprocess
import signal
import os

# Iniciar servidor Django
print("Iniciando servidor Django...")
server_process = subprocess.Popen(
    ["python", "manage.py", "runserver", "8002"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="/Users/pedropablosanintrujillo/GitHub/Inventario"
)

# Esperar a que inicie el servidor
time.sleep(3)

BASE_URL = "http://127.0.0.1:8002"

def test_endpoint(method, endpoint, data=None, description=""):
    """Probar un endpoint de API"""
    url = BASE_URL + endpoint
    print(f"\n{'='*60}")
    print(f"Probando: {description}")
    print(f"Método: {method}")
    print(f"URL: {url}")
    
    response = None
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=5)
        
        if response is not None:
            print(f"Código de Estado: {response.status_code}")
            print("Respuesta:")
            print(json.dumps(response.json(), indent=2))
            return response.status_code == 200 or response.status_code == 201
        else:
            print("No response received.")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False
    except json.JSONDecodeError:
        if response is not None:
            print(f"Invalid JSON response: {response.text}")
        else:
            print("Invalid JSON response: No response object.")
        return False

def run_tests():
    """Ejecutar todas las pruebas de API"""
    print("Iniciando Pruebas de API para Sistema de Gestión de Inventario")
    
    tests_passed = 0
    total_tests = 0
    
    # Prueba 1: Obtener todos los productos
    total_tests += 1
    if test_endpoint("GET", "/api/productos/", description="Obtener todos los productos"):
        tests_passed += 1
    
    # Prueba 2: Obtener producto específico
    total_tests += 1
    if test_endpoint("GET", "/api/productos/1/", description="Obtener producto por ID"):
        tests_passed += 1
    
    # Prueba 3: Obtener todas las bodegas
    total_tests += 1
    if test_endpoint("GET", "/api/bodegas/", description="Obtener todas las bodegas"):
        tests_passed += 1
    
    # Prueba 4: Obtener inventario de bodega
    total_tests += 1
    if test_endpoint("GET", "/api/bodegas/1/inventario/", description="Obtener inventario de bodega"):
        tests_passed += 1
    
    # Prueba 5: Obtener artículos de un producto
    total_tests += 1
    if test_endpoint("GET", "/api/productos/1/articulos/", description="Obtener artículos de producto"):
        tests_passed += 1
    
    # Prueba 6: Crear un nuevo producto
    total_tests += 1
    new_product = {
        "nombre": "Producto de Prueba API",
        "sku": "TEST-API-001",
        "precio_costo": 50.00,
        "precio_venta": 75.00,
        "descripcion": "Producto creado via prueba API",
        "stock_minimo": 5,
        "stock_maximo": 100
    }
    if test_endpoint("POST", "/api/productos/crear/", new_product, "Crear nuevo producto"):
        tests_passed += 1
    
    # Prueba 7: Agregar nuevo artículo
    total_tests += 1
    new_article = {
        "producto_id": 1,
        "bodega_id": 1,
        "numero_serie": "TEST123456",
        "codigo_barras": "1234567890123"
    }
    if test_endpoint("POST", "/api/articulos/agregar/", new_article, "Agregar nuevo artículo"):
        tests_passed += 1
    
    # Prueba 8: Actualizar estado de artículo
    total_tests += 1
    update_data = {
        "estado": "vendido",
        "motivo": "Venta realizada via prueba API"
    }
    if test_endpoint("PUT", "/api/articulos/1/estado/", update_data, "Actualizar estado de artículo"):
        tests_passed += 1
    
    # Prueba 9: Obtener movimientos de artículo
    total_tests += 1
    if test_endpoint("GET", "/api/articulos/1/movimientos/", description="Obtener movimientos de artículo"):
        tests_passed += 1
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN DE PRUEBAS")
    print(f"{'='*60}")
    print(f"Pruebas exitosas: {tests_passed}/{total_tests}")
    print(f"Pruebas fallidas: {total_tests - tests_passed}/{total_tests}")
    print(f"Tasa de éxito: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n¡Todas las pruebas pasaron! Tu API está funcionando correctamente.")
    else:
        print(f"\n{total_tests - tests_passed} prueba(s) fallaron. Por favor verifica la implementación de la API.")

if __name__ == "__main__":
    try:
        run_tests()
    finally:
        # Limpiar: detener el servidor
        print("\nDeteniendo servidor Django...")
        server_process.terminate()
        server_process.wait()
        print("Servidor detenido.")