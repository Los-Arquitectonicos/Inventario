#!/usr/bin/env python3
"""
Test script for inventory API endpoints
"""
import requests
import json
import time
import subprocess
import signal
import os

# Start Django server
print("Starting Django server...")
server_process = subprocess.Popen(
    ["python", "manage.py", "runserver", "8002"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="/Users/pedropablosanintrujillo/GitHub/Inventario"
)

# Wait for server to start
time.sleep(3)

BASE_URL = "http://127.0.0.1:8002"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test an API endpoint"""
    url = BASE_URL + endpoint
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Method: {method}")
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
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return response.status_code == 200 or response.status_code == 201
        else:
            print("❌ No response received.")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False
    except json.JSONDecodeError:
        if response is not None:
            print(f"❌ Invalid JSON response: {response.text}")
        else:
            print("❌ Invalid JSON response: No response object.")
        return False

def run_tests():
    """Run all API tests"""
    print("🚀 Starting API Tests for Inventory Management System")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Get all products
    total_tests += 1
    if test_endpoint("GET", "/api/productos/", description="Get all products"):
        tests_passed += 1
    
    # Test 2: Get specific product
    total_tests += 1
    if test_endpoint("GET", "/api/productos/1/", description="Get product by ID"):
        tests_passed += 1
    
    # Test 3: Get all warehouses
    total_tests += 1
    if test_endpoint("GET", "/api/bodegas/", description="Get all warehouses"):
        tests_passed += 1
    
    # Test 4: Get warehouse inventory
    total_tests += 1
    if test_endpoint("GET", "/api/bodegas/1/inventario/", description="Get warehouse inventory"):
        tests_passed += 1
    
    # Test 5: Get articles for a product
    total_tests += 1
    if test_endpoint("GET", "/api/productos/1/articulos/", description="Get articles for product"):
        tests_passed += 1
    
    # Test 6: Create a new product
    total_tests += 1
    new_product = {
        "nombre": "Test Product API",
        "sku": "TEST-API-001",
        "precio_costo": 50.00,
        "precio_venta": 75.00,
        "descripcion": "Product created via API test",
        "stock_minimo": 5,
        "stock_maximo": 100
    }
    if test_endpoint("POST", "/api/productos/crear/", new_product, "Create new product"):
        tests_passed += 1
    
    # Test 7: Add new article
    total_tests += 1
    new_article = {
        "producto_id": 1,
        "bodega_id": 1,
        "numero_serie": "TEST123456",
        "codigo_barras": "1234567890123"
    }
    if test_endpoint("POST", "/api/articulos/agregar/", new_article, "Add new article"):
        tests_passed += 1
    
    # Test 8: Update article status
    total_tests += 1
    update_data = {
        "estado": "vendido",
        "motivo": "Venta realizada via API test"
    }
    if test_endpoint("PUT", "/api/articulos/1/estado/", update_data, "Update article status"):
        tests_passed += 1
    
    # Test 9: Get article movements
    total_tests += 1
    if test_endpoint("GET", "/api/articulos/1/movimientos/", description="Get article movements"):
        tests_passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🏁 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    print(f"❌ Tests failed: {total_tests - tests_passed}/{total_tests}")
    print(f"Success rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 All tests passed! Your API is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed. Please check the API implementation.")

if __name__ == "__main__":
    try:
        run_tests()
    finally:
        # Clean up: stop the server
        print("\n🛑 Stopping Django server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")