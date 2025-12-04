"""
Script para obtener el token CSRF de Django y actualizar la colección Postman.

Uso:
    python3 obtener_csrf_token.py
"""

import requests
import json
import urllib3
import re

# Desactivar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ALB_URL = "https://provesi-alb-2028908830.us-east-1.elb.amazonaws.com"
BASE_URL = f"{ALB_URL}/inventario"


def obtener_csrf_token():
    """Obtiene el token CSRF haciendo GET a cualquier página de Django."""
    
    print("🔐 Obteniendo token CSRF de Django...\n")
    
    try:
        # Crear sesión persistente
        session = requests.Session()
        
        # Método 1: Intentar endpoint de login para forzar cookie CSRF
        endpoints_a_probar = [
            f"{BASE_URL}/auth/login/",
            f"{BASE_URL}/admin/login/",
            f"{BASE_URL}/",
        ]
        
        csrf_token = None
        for endpoint in endpoints_a_probar:
            try:
                print(f"📡 Probando: {endpoint}")
                response = session.get(endpoint, verify=False, allow_redirects=True, timeout=10)
                
                # Obtener token de cookie
                csrf_token = session.cookies.get('csrftoken')
                
                # Si no está en cookies, buscar en HTML
                if not csrf_token and response.status_code == 200:
                    # Buscar input hidden con csrfmiddlewaretoken
                    match = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)["\']', response.text)
                    if not match:
                        match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrfmiddlewaretoken["\']', response.text)
                    if match:
                        csrf_token = match.group(1)
                        # Establecer la cookie manualmente
                        session.cookies.set('csrftoken', csrf_token)
                
                if csrf_token:
                    print(f"✅ Token obtenido de: {endpoint}\n")
                    break
                    
            except Exception as e:
                print(f"⚠️  Error en {endpoint}: {e}")
                continue
        
        if not csrf_token:
            print("❌ No se pudo obtener token CSRF de Django")
            print("💡 Intenta:")
            print("   1. Verificar que Django esté corriendo")
            print("   2. Verificar que CSRF middleware esté habilitado")
            print("   3. Acceder manualmente a la URL y copiar el token\n")
            return None
        
        print(f"✅ Token CSRF: {csrf_token[:20]}...{csrf_token[-10:]}")
        print(f"🍪 Cookies: {dict(session.cookies)}\n")
        return csrf_token, session.cookies

        # Actualizar colección Postman automáticamente
        actualizar_coleccion_postman(csrf_token)
        
        # Instrucciones
        print("=" * 70)
        print("CONFIGURACIÓN COMPLETADA")
        print("=" * 70)
        print("\n✅ Colección Postman actualizada con:")
        print(f"   - X-CSRFToken: {csrf_token[:20]}...")
        print(f"   - Referer: {ALB_URL}/inventario/")
        print(f"   - Cookie: csrftoken={csrf_token[:20]}...\n")
        print("📁 Archivo generado: postman_datos_completos.json")
        print("\n⚠️  IMPORTANTE en Postman:")
        print("   Settings → General → SSL certificate verification: OFF\n")
        print("=" * 70 + "\n")
        
        return csrf_token, cookies
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def actualizar_coleccion_postman(csrf_token):
    """Actualiza la colección Postman con el token CSRF y headers."""
    
    try:
        # Leer colección existente
        with open("postman_datos_completos.json", "r") as f:
            coleccion = json.load(f)
        
        # Agregar headers a cada request
        for item in coleccion["item"]:
            if "request" in item:
                # Asegurar que existe array de headers
                if "header" not in item["request"]:
                    item["request"]["header"] = []
                
                headers_existentes = {h["key"]: h for h in item["request"]["header"]}
                
                # Agregar/actualizar headers necesarios
                headers_necesarios = [
                    {"key": "X-CSRFToken", "value": csrf_token, "type": "text"},
                    {"key": "Referer", "value": f"{ALB_URL}/inventario/", "type": "text"},
                    {"key": "Cookie", "value": f"csrftoken={csrf_token}", "type": "text"}
                ]
                
                for header in headers_necesarios:
                    if header["key"] in headers_existentes:
                        headers_existentes[header["key"]]["value"] = header["value"]
                    else:
                        item["request"]["header"].append(header)
        
        # Guardar colección actualizada
        with open("postman_datos_completos.json", "w") as f:
            json.dump(coleccion, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Colección actualizada con {len(coleccion['item'])} requests\n")
        
    except FileNotFoundError:
        print("⚠️  No se encontró postman_datos_completos.json")
        print("   Ejecuta primero: python3 generar_postman_datos_completos.py\n")
    except Exception as e:
        print(f"❌ Error actualizando colección: {e}\n")


def probar_con_csrf(csrf_token, cookies):
    """Prueba crear un producto con el token CSRF."""
    
    print("=" * 70)
    print("PRUEBA DE CREACIÓN DE PRODUCTO")
    print("=" * 70 + "\n")
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Referer": f"{ALB_URL}/inventario/",
        "Content-Type": "application/json",
        "Cookie": f"csrftoken={csrf_token}"
    }
    
    payload = {
        "nombre": "Producto Prueba CSRF",
        "descripcion": "Prueba con token CSRF",
        "precio_costo": "10000",
        "precio_venta": "15000",
        "peso": "1.0",
        "dimensiones": "10x10x10",
        "color": "Negro",
        "talla": "Universal",
        "marca": "Test",
        "cantidad_stock": 100
    }
    
    print("📤 POST /productos/crear/...\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/productos/crear/",
            headers=headers,
            json=payload,
            verify=False
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Producto creado exitosamente!")
            print(f"Response: {response.json()}\n")
        else:
            print(f"❌ Error: {response.text[:200]}\n")
            
    except Exception as e:
        print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    result = obtener_csrf_token()
    
    if result:
        csrf_token, cookies = result
        
        # Actualizar colección Postman automáticamente
        print("📝 Actualizando colección Postman...")
        actualizar_coleccion_postman(csrf_token)
        
        print("\n✅ Proceso completado!")
        print(f"   - Token CSRF: {csrf_token[:30]}...")
        print(f"   - Colección actualizada: postman_datos_completos.json")
        print(f"   - Ahora puedes importar la colección en Postman\n")
    else:
        print("\n❌ No se pudo obtener el token CSRF")
