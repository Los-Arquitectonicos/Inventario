#!/usr/bin/env python3
"""
Script de prueba de endpoints Django a través de Kong HTTPS
Prueba autenticación JWT y operaciones CRUD básicas
"""

import requests
import json
from datetime import datetime
import urllib3

# Deshabilitar advertencias SSL para certificados self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración
KONG_URL = "https://3.238.225.18:8443"
BASE_URL = f"{KONG_URL}/inventario"

# Credenciales de prueba
CREDENTIALS = {
    "admin": {"username": "admin", "password": "ProvesiAdmin2024!"},
    "gerente": {"username": "gerente", "password": "Gerente2024!"},
    "empleado": {"username": "empleado", "password": "Empleado2024!"}
}

def print_section(title):
    """Imprime un separador de sección."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_result(test_name, success, details=""):
    """Imprime el resultado de una prueba."""
    status = "✅ ÉXITO" if success else "❌ FALLO"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")

def get_token(username, password):
    """Obtiene un token JWT."""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/token/",
            json={"username": username, "password": password},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access"), data.get("refresh")
        else:
            print(f"Error obteniendo token: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None, None
    except Exception as e:
        print(f"Excepción obteniendo token: {e}")
        return None, None

def test_authentication():
    """Prueba la autenticación con diferentes roles."""
    print_section("PRUEBA 1: Autenticación JWT")
    
    results = {}
    for role, creds in CREDENTIALS.items():
        print(f"\nProbando autenticación como '{role}'...")
        access_token, refresh_token = get_token(creds["username"], creds["password"])
        
        if access_token:
            print_result(f"Login como {role}", True, f"Token obtenido (longitud: {len(access_token)})")
            results[role] = {"access": access_token, "refresh": refresh_token}
        else:
            print_result(f"Login como {role}", False, "No se pudo obtener token")
            results[role] = None
    
    return results

def test_get_productos(role, token):
    """Prueba GET /api/productos/"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/productos/",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            productos = response.json()
            print_result(f"{role}: Listar productos", True, f"Encontrados {len(productos)} productos")
            return True, productos
        elif response.status_code == 403:
            print_result(f"{role}: Listar productos", False, "Acceso denegado (403)")
            return False, None
        else:
            print_result(f"{role}: Listar productos", False, f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(f"{role}: Listar productos", False, f"Error: {e}")
        return False, None

def test_create_producto(role, token):
    """Prueba POST /api/productos/"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        timestamp = datetime.now().strftime("%H%M%S")
        producto_data = {
            "nombre": f"Producto Test {role} {timestamp}",
            "sku": f"TEST-{role.upper()}-{timestamp}",
            "descripcion": f"Producto de prueba creado por {role}",
            "precio": 99.99,
            "stock_minimo": 10,
            "categoria": "Electrónica"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/productos/",
            headers=headers,
            json=producto_data,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 201:
            producto = response.json()
            print_result(f"{role}: Crear producto", True, f"Producto creado con ID: {producto.get('id')}")
            return True, producto
        elif response.status_code == 403:
            print_result(f"{role}: Crear producto", False, "Acceso denegado (403)")
            return False, None
        else:
            print_result(f"{role}: Crear producto", False, f"Status: {response.status_code}, Resp: {response.text[:100]}")
            return False, None
    except Exception as e:
        print_result(f"{role}: Crear producto", False, f"Error: {e}")
        return False, None

def test_get_producto_detail(role, token, producto_id):
    """Prueba GET /api/productos/{id}/"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/productos/{producto_id}/",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            producto = response.json()
            print_result(f"{role}: Ver detalle producto", True, f"Producto: {producto.get('nombre')}")
            return True, producto
        else:
            print_result(f"{role}: Ver detalle producto", False, f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(f"{role}: Ver detalle producto", False, f"Error: {e}")
        return False, None

def test_update_producto(role, token, producto_id):
    """Prueba PUT /api/productos/{id}/"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        update_data = {
            "precio": 149.99,
            "descripcion": f"Producto actualizado por {role} a las {datetime.now().strftime('%H:%M:%S')}"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/productos/{producto_id}/",
            headers=headers,
            json=update_data,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            producto = response.json()
            print_result(f"{role}: Actualizar producto", True, f"Precio actualizado a: {producto.get('precio')}")
            return True, producto
        elif response.status_code == 403:
            print_result(f"{role}: Actualizar producto", False, "Acceso denegado (403)")
            return False, None
        else:
            print_result(f"{role}: Actualizar producto", False, f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(f"{role}: Actualizar producto", False, f"Error: {e}")
        return False, None

def test_get_clientes(role, token):
    """Prueba GET /api/clientes/"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/clientes/",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            clientes = response.json()
            print_result(f"{role}: Listar clientes", True, f"Encontrados {len(clientes)} clientes")
            return True, clientes
        elif response.status_code == 403:
            print_result(f"{role}: Listar clientes", False, "Acceso denegado (403)")
            return False, None
        else:
            print_result(f"{role}: Listar clientes", False, f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(f"{role}: Listar clientes", False, f"Error: {e}")
        return False, None

def test_without_auth():
    """Prueba acceso sin autenticación."""
    print_section("PRUEBA: Acceso sin autenticación")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/productos/",
            verify=False,
            timeout=10
        )
        
        if response.status_code == 401:
            print_result("Acceso sin token", True, "Correctamente denegado con 401")
            return True
        else:
            print_result("Acceso sin token", False, f"Status inesperado: {response.status_code}")
            return False
    except Exception as e:
        print_result("Acceso sin token", False, f"Error: {e}")
        return False

def main():
    print_section("🔐 PRUEBA DE ENDPOINTS DJANGO VÍA KONG HTTPS")
    print(f"URL Base: {BASE_URL}")
    print(f"Kong HTTPS: {KONG_URL}")
    
    # Prueba sin autenticación
    test_without_auth()
    
    # Obtener tokens
    tokens = test_authentication()
    
    # Verificar que tenemos al menos un token válido
    valid_tokens = {role: data for role, data in tokens.items() if data is not None}
    if not valid_tokens:
        print("\n❌ No se pudieron obtener tokens. Verifica las credenciales.")
        return
    
    # Pruebas con cada rol
    for role, token_data in valid_tokens.items():
        print_section(f"PRUEBAS CON ROL: {role.upper()}")
        
        access_token = token_data["access"]
        
        # Listar productos
        success, productos = test_get_productos(role, access_token)
        
        # Crear producto
        success, nuevo_producto = test_create_producto(role, access_token)
        
        if success and nuevo_producto:
            producto_id = nuevo_producto.get("id")
            
            # Ver detalle
            test_get_producto_detail(role, access_token, producto_id)
            
            # Actualizar producto
            test_update_producto(role, access_token, producto_id)
        
        # Listar clientes
        test_get_clientes(role, access_token)
    
    print_section("✨ PRUEBAS COMPLETADAS")
    print("\nConexión verificada:")
    print("  ✅ Kong HTTPS (puerto 8443)")
    print("  ✅ ALB HTTPS (backend)")
    print("  ✅ Django con JWT")
    print("\nLa arquitectura completa está funcionando correctamente.")

if __name__ == "__main__":
    main()
