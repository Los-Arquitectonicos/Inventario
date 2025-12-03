#!/usr/bin/env python3
"""
Script para probar el servicio de notificaciones paso a paso
"""

import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KONG_URL = "https://3.238.225.18:8443"
BASE_URL = f"{KONG_URL}/notifications"

def test_endpoint(name, method, path, data=None, headers=None):
    """Prueba un endpoint y muestra el resultado."""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Método: {method}")
    print(f"URL: {url}")
    
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    if headers:
        print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, verify=False, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, verify=False, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, verify=False, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        
        return response
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

print("="*60)
print("  PRUEBA DIRECTA DEL SERVICIO DE NOTIFICACIONES")
print("="*60)

# 1. Health Check
response = test_endpoint("Health Check", "GET", "/health")

if not response or response.status_code != 200:
    print("\n❌ El servicio no está respondiendo correctamente")
    exit(1)

# 2. Login
print("\n" + "="*60)
print("  Autenticación")
print("="*60)

login_data = {
    "username": "admin",
    "password": "admin123"
}

response = test_endpoint("Login como admin", "POST", "/auth/login", data=login_data)

if not response or response.status_code != 200:
    print("\n❌ No se pudo autenticar")
    exit(1)

token = response.json().get("access_token")
print(f"\n✅ Token obtenido: {token[:50]}...")

headers = {"Authorization": f"Bearer {token}"}

# 3. Listar usuarios
test_endpoint("Listar usuarios", "GET", "/users", headers=headers)

# 4. Enviar notificación a operario1
notification_data = {
    "message": "🔔 Prueba de notificación directa - Admin a Operario1",
    "recipient_username": "operario1"
}

test_endpoint("Enviar notificación a operario1", "POST", "/send", 
              data=notification_data, headers=headers)

# 5. Login como operario1
print("\n" + "="*60)
print("  Ver notificaciones de Operario1")
print("="*60)

login_data_op = {
    "username": "operario1",
    "password": "operario123"
}

response = test_endpoint("Login como operario1", "POST", "/auth/login", 
                         data=login_data_op)

if response and response.status_code == 200:
    token_op = response.json().get("access_token")
    headers_op = {"Authorization": f"Bearer {token_op}"}
    
    # 6. Ver notificaciones de operario1
    response = test_endpoint("Ver mis notificaciones (operario1)", "GET", "/inbox", 
                             headers=headers_op)
    
    if response and response.status_code == 200:
        notificaciones = response.json()
        print(f"\n📬 Total de notificaciones: {len(notificaciones)}")
        print("\nÚltimas 3 notificaciones:")
        for i, notif in enumerate(notificaciones[:3], 1):
            estado = "📭 Leída" if notif.get("read") else "📬 No leída"
            print(f"\n{i}. {estado}")
            print(f"   ID: {notif.get('id')}")
            print(f"   De: {notif.get('sender_username')}")
            print(f"   Mensaje: {notif.get('message')[:80]}...")
            print(f"   Fecha: {notif.get('sent_at')}")

print("\n" + "="*60)
print("  ✅ PRUEBAS COMPLETADAS")
print("="*60)
