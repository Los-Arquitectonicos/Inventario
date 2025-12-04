#!/usr/bin/env python
"""
Script para verificar si el endpoint de clientes funciona correctamente
"""
import requests
import urllib3

# Deshabilitar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración
PROVESI_API_URL = "https://provesi-alb-2028908830.us-east-1.elb.amazonaws.com"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def obtener_token():
    """Obtener token JWT para autenticación"""
    print("\n🔐 Obteniendo token JWT...")
    
    url = f"{PROVESI_API_URL}/inventario/auth/login/"
    data = {
        "username": ADMIN_USER,
        "password": ADMIN_PASS
    }
    
    try:
        response = requests.post(url, json=data, verify=False, timeout=10)
        
        if response.status_code == 200:
            json_data = response.json()
            token = json_data.get('access')
            if token:
                print("✅ Token obtenido correctamente")
                return token
            else:
                print(f"❌ No se encontró 'access' en la respuesta: {json_data}")
                return None
        else:
            print(f"❌ Error al obtener token: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def verificar_endpoint_cliente(cliente_id, token):
    """Verificar que el endpoint /api/clientes/<id>/ funcione"""
    print(f"\n🔍 Verificando endpoint para cliente ID {cliente_id}...")
    
    url = f"{PROVESI_API_URL}/inventario/api/clientes/{cliente_id}/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Cliente encontrado:")
            print(f"      ID: {data.get('id')}")
            print(f"      Nombre: {data.get('nombre')}")
            print(f"      Email: {data.get('email')}")
            print(f"      Ciudad: {data.get('ciudad')}")
            return True
        elif response.status_code == 404:
            print(f"   ⚠️  Cliente {cliente_id} no existe en la base de datos")
            return False
        else:
            print(f"   ❌ Error inesperado: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def listar_todos_clientes(token):
    """Listar todos los clientes disponibles"""
    print(f"\n📋 Listando todos los clientes...")
    
    url = f"{PROVESI_API_URL}/inventario/api/clientes/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            clientes = data.get('clientes', [])
            
            if clientes:
                print(f"   ✅ Se encontraron {len(clientes)} clientes:")
                print(f"\n   {'ID':<5} {'Nombre':<30} {'Email':<30}")
                print("   " + "-" * 65)
                
                for cliente in clientes[:10]:  # Mostrar solo los primeros 10
                    print(f"   {cliente.get('id'):<5} {cliente.get('nombre'):<30} {cliente.get('email'):<30}")
                
                if len(clientes) > 10:
                    print(f"   ... y {len(clientes) - 10} más")
            else:
                print("   ⚠️  No hay clientes en la base de datos")
            
            return clientes
        else:
            print(f"   ❌ Error al listar: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return []

def main():
    print("\n" + "="*70)
    print("VERIFICACIÓN DE ENDPOINTS DE CLIENTES")
    print("="*70)
    
    # Obtener token
    token = obtener_token()
    if not token:
        print("\n❌ No se pudo obtener el token. Verifica las credenciales.")
        return
    
    # Listar todos los clientes
    clientes = listar_todos_clientes(token)
    
    # Verificar clientes específicos
    print("\n" + "-"*70)
    verificar_endpoint_cliente(1, token)
    verificar_endpoint_cliente(2, token)
    verificar_endpoint_cliente(99999, token)  # Cliente inexistente
    
    print("\n" + "="*70)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
