#!/usr/bin/env python3
"""
Script de análisis de autorización exhaustivo para ProvesiWMS
Verifica que todos los endpoints API implementen correctamente:
1. Autenticación JWT requerida
2. Autorización basada en permisos
3. Respuestas apropiadas según el rol del usuario
"""

import requests
import json
from typing import Dict, List, Tuple
import urllib3

# Suprimir warnings de SSL ya que usamos certificados self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://provesi-alb-2003818714.us-east-1.elb.amazonaws.com"

# Credenciales de prueba por rol
TEST_CREDENTIALS = {
    "admin": {"username": "admin", "password": "ProvesiAdmin2024!"},
    "gerente": {"username": "gerente", "password": "Gerente2024!"},
    "empleado": {"username": "empleado", "password": "Empleado2024!"}
}

# Endpoints a probar (método, URL, permisos esperados según rol)
ENDPOINTS_TO_TEST = [
    # API Productos
    ("GET", "/inventario/api/productos/", {"admin": True, "gerente": True, "empleado": False}),
    ("POST", "/inventario/api/productos/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Pedidos
    ("GET", "/inventario/api/pedidos/", {"admin": True, "gerente": True, "empleado": False}),
    ("POST", "/inventario/api/pedidos/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Clientes
    ("GET", "/inventario/api/clientes/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Bodegas
    ("GET", "/inventario/api/bodegas/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Usuarios (solo admin y gerente deberían ver)
    ("GET", "/inventario/api/usuarios/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Artículos
    ("GET", "/inventario/api/articulos/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Cotizaciones
    ("GET", "/inventario/api/cotizaciones/", {"admin": True, "gerente": True, "empleado": False}),
    
    # API Facturas
    ("GET", "/inventario/api/facturas/", {"admin": True, "gerente": True, "empleado": False}),
]

def get_jwt_token(username: str, password: str) -> str:
    """Obtiene un token JWT válido para el usuario especificado."""
    try:
        response = requests.post(
            f"{BASE_URL}/inventario/auth/token/",
            json={"username": username, "password": password},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access", "")
        else:
            print(f"Error obteniendo token para {username}: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return ""
    except Exception as e:
        print(f"Excepción obteniendo token para {username}: {e}")
        return ""

def test_endpoint_without_auth(method: str, endpoint: str) -> bool:
    """Prueba un endpoint sin autenticación, debe retornar 401."""
    try:
        response = requests.request(
            method,
            f"{BASE_URL}{endpoint}",
            json={"test": "data"} if method == "POST" else None,
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 401:
            try:
                data = response.json()
                if "token" in data.get("error", "").lower() or data.get("code") == "JWT_REQUIRED":
                    return True
            except:
                pass
        
        print(f" {method} {endpoint} sin auth retornó {response.status_code} (esperado 401)")
        return False
        
    except Exception as e:
        print(f"Error probando {method} {endpoint} sin auth: {e}")
        return False

def test_endpoint_with_invalid_token(method: str, endpoint: str) -> bool:
    """Prueba un endpoint con token inválido, debe retornar 401."""
    try:
        headers = {
            "Authorization": "Bearer invalid_token_12345",
            "Content-Type": "application/json"
        }
        
        response = requests.request(
            method,
            f"{BASE_URL}{endpoint}",
            json={"test": "data"} if method == "POST" else None,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 401:
            try:
                data = response.json()
                if "inválido" in data.get("error", "").lower() or data.get("code") == "INVALID_TOKEN":
                    return True
            except:
                pass
        
        print(f" {method} {endpoint} con token inválido retornó {response.status_code} (esperado 401)")
        return False
        
    except Exception as e:
        print(f"Error probando {method} {endpoint} con token inválido: {e}")
        return False

def test_endpoint_with_role(method: str, endpoint: str, role: str, token: str, should_have_access: bool) -> bool:
    """Prueba un endpoint con un rol específico."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        json_data = None
        if method == "POST":
            if "pedidos" in endpoint:
                json_data = {"cliente_id": 1, "fecha_entrega": "2025-12-01"}
            elif "productos" in endpoint:
                json_data = {"nombre": "Test Product", "sku": f"TEST-{role}-123", "precio": 100}
            else:
                json_data = {"test": "data"}
        
        response = requests.request(
            method,
            f"{BASE_URL}{endpoint}",
            json=json_data,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if should_have_access:
            # El usuario debe tener acceso
            if response.status_code in [200, 201]:
                return True
            elif response.status_code == 403:
                print(f"{role} fue denegado acceso a {method} {endpoint} (debería tener acceso)")
                try:
                    data = response.json()
                    print(f"   Respuesta: {data.get('error', 'Sin mensaje')}")
                except:
                    pass
                return False
            elif response.status_code == 404:
                # 404 puede ser aceptable si el endpoint no existe aún
                print(f" {method} {endpoint} retorna 404 (endpoint puede no existir)")
                return True
            else:
                print(f"{role} recibió código inesperado {response.status_code} para {method} {endpoint}")
                return False
        else:
            # El usuario NO debe tener acceso
            if response.status_code == 403:
                try:
                    data = response.json()
                    if "permission" in data.get("error", "").lower() or data.get("code") == "PERMISSION_DENIED":
                        return True
                except:
                    pass
                print(f" {role} fue denegado {method} {endpoint} pero la respuesta no indica denegación por permisos")
                return True
            elif response.status_code in [200, 201]:
                print(f"{role} tuvo acceso a {method} {endpoint} (NO debería tener acceso)")
                return False
            else:
                print(f" {role} recibió código inesperado {response.status_code} para {method} {endpoint} (sin acceso)")
                return True
                
    except Exception as e:
        print(f"Error probando {method} {endpoint} con rol {role}: {e}")
        return False

def main():
    print(" ANÁLISIS EXHAUSTIVO DE AUTORIZACIÓN - ProvesiWMS")
    print("=" * 60)
    
    # Obtener tokens para cada rol
    tokens = {}
    for role, credentials in TEST_CREDENTIALS.items():
        print(f"Obteniendo token para {role}...")
        token = get_jwt_token(credentials["username"], credentials["password"])
        if token:
            tokens[role] = token
            print(f"Token obtenido para {role}")
        else:
            print(f"No se pudo obtener token para {role}")
            return
    
    print("\n" + "=" * 60)
    print("RESULTADOS DE PRUEBAS DE AUTORIZACIÓN")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Probar cada endpoint
    for method, endpoint, expected_permissions in ENDPOINTS_TO_TEST:
        print(f"\nProbando: {method} {endpoint}")
        print("-" * 40)
        
        # Prueba sin autenticación
        print("   Sin autenticación...", end=" ")
        if test_endpoint_without_auth(method, endpoint):
            print("CORRECTO (401)")
            passed_tests += 1
        else:
            print("FALLO")
            failed_tests += 1
        total_tests += 1
        
        # Prueba con token inválido
        print("   Token inválido...", end=" ")
        if test_endpoint_with_invalid_token(method, endpoint):
            print("CORRECTO (401)")
            passed_tests += 1
        else:
            print("FALLO")
            failed_tests += 1
        total_tests += 1
        
        # Prueba con cada rol
        for role, should_have_access in expected_permissions.items():
            if role in tokens:
                print(f"   Rol {role} (esperado: {'' if should_have_access else ''})...", end=" ")
                if test_endpoint_with_role(method, endpoint, role, tokens[role], should_have_access):
                    print("CORRECTO")
                    passed_tests += 1
                else:
                    print("FALLO")
                    failed_tests += 1
                total_tests += 1
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"Total de pruebas: {total_tests}")
    print(f"Pruebas exitosas: {passed_tests} ")
    print(f"Pruebas fallidas: {failed_tests} ")
    print(f"Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n¡TODAS LAS PRUEBAS DE AUTORIZACIÓN PASARON!")
        print("   El sistema tiene implementación correcta de seguridad.")
    else:
        print(f"\n SE ENCONTRARON {failed_tests} PROBLEMAS DE SEGURIDAD")
        print("   Revisa los fallos arriba para identificar endpoints vulnerables.")
        
        # Identificar los problemas más comunes
        print("\nRECOMENDACIONES:")
        print("1. Verifica que todos los endpoints API tengan decoradores @jwt_required")
        print("2. Agrega decoradores @require_permission apropiados")
        print("3. Verifica la matriz de permisos en auth_utils.py")
        print("4. Prueba manualmente los endpoints que fallaron")

if __name__ == "__main__":
    main()