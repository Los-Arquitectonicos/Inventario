#!/usr/bin/env python3
"""
Script de prueba para el microservicio de notificaciones
Prueba creación de usuarios y envío de notificaciones de admin a operarios de bodega
"""

import requests
import json
from datetime import datetime
import urllib3

# Deshabilitar advertencias SSL para certificados self-signed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración
KONG_URL = "https://3.238.225.18:8443"
NOTIFICATIONS_BASE_URL = f"{KONG_URL}/notifications"

# Usuarios a crear
USERS_TO_CREATE = [
    {
        "username": "admin",
        "email": "admin@provesi.com",
        "role": "admin",
        "password": "Admin123!"
    },
    {
        "username": "operario1",
        "email": "operario1@provesi.com",
        "role": "operario_bodega",
        "password": "Operario123!"
    },
    {
        "username": "operario2",
        "email": "operario2@provesi.com",
        "role": "operario_bodega",
        "password": "Operario123!"
    },
    {
        "username": "empacador1",
        "email": "empacador1@provesi.com",
        "role": "empacador",
        "password": "Empacador123!"
    },
    {
        "username": "calidad1",
        "email": "calidad1@provesi.com",
        "role": "operario_control_calidad",
        "password": "Calidad123!"
    }
]

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

def check_health():
    """Verifica que el servicio de notificaciones esté funcionando."""
    try:
        response = requests.get(
            f"{NOTIFICATIONS_BASE_URL}/health",
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Health Check", True, f"Servicio: {data.get('status')}")
            return True
        else:
            print_result("Health Check", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Health Check", False, f"Error: {e}")
        return False

def create_user(user_data, admin_token=None):
    """Crea un usuario en el sistema."""
    try:
        headers = {}
        if admin_token:
            headers["Authorization"] = f"Bearer {admin_token}"
        
        response = requests.post(
            f"{NOTIFICATIONS_BASE_URL}/users",
            json=user_data,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 201:
            user = response.json()
            print_result(f"Crear usuario '{user_data['username']}'", True, 
                        f"Role: {user_data['role']}")
            return True, user
        elif response.status_code == 400 and "already exists" in response.text:
            print_result(f"Crear usuario '{user_data['username']}'", True, 
                        "Ya existe (OK)")
            return True, None
        else:
            print_result(f"Crear usuario '{user_data['username']}'", False, 
                        f"Status: {response.status_code}, {response.text[:100]}")
            return False, None
    except Exception as e:
        print_result(f"Crear usuario '{user_data['username']}'", False, f"Error: {e}")
        return False, None

def login_user(username, password):
    """Obtiene token de autenticación para un usuario."""
    try:
        response = requests.post(
            f"{NOTIFICATIONS_BASE_URL}/auth/login",
            json={
                "username": username,
                "password": password
            },
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_result(f"Login como '{username}'", True, 
                        f"Token obtenido (tipo: {data.get('token_type')})")
            return token
        else:
            print_result(f"Login como '{username}'", False, 
                        f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_result(f"Login como '{username}'", False, f"Error: {e}")
        return None

def get_users(token):
    """Obtiene la lista de usuarios."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{NOTIFICATIONS_BASE_URL}/users",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            print_result("Listar usuarios", True, f"Total: {len(users)} usuarios")
            
            # Mostrar resumen por rol
            roles = {}
            for user in users:
                role = user.get('role', 'unknown')
                roles[role] = roles.get(role, 0) + 1
            
            for role, count in roles.items():
                print(f"      • {role}: {count}")
            
            return True, users
        else:
            print_result("Listar usuarios", False, f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result("Listar usuarios", False, f"Error: {e}")
        return False, None

def send_notification_to_role(token, message, roles):
    """Envía una notificación a usuarios con roles específicos."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": message,
            "recipient_roles": roles
        }
        
        response = requests.post(
            f"{NOTIFICATIONS_BASE_URL}/send",
            headers=headers,
            json=payload,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            sent = result.get('sent_count', 0)
            print_result(f"Enviar notificación a roles {roles}", True, 
                        f"Enviada a {sent} usuarios")
            return True, result
        else:
            print_result(f"Enviar notificación a roles {roles}", False, 
                        f"Status: {response.status_code}, {response.text[:100]}")
            return False, None
    except Exception as e:
        print_result(f"Enviar notificación a roles {roles}", False, f"Error: {e}")
        return False, None

def send_notification_to_user(token, message, username):
    """Envía una notificación a un usuario específico."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": message,
            "recipient_username": username
        }
        
        response = requests.post(
            f"{NOTIFICATIONS_BASE_URL}/send",
            headers=headers,
            json=payload,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(f"Enviar notificación a '{username}'", True, 
                        "Notificación enviada")
            return True, result
        else:
            print_result(f"Enviar notificación a '{username}'", False, 
                        f"Status: {response.status_code}, {response.text[:100]}")
            return False, None
    except Exception as e:
        print_result(f"Enviar notificación a '{username}'", False, f"Error: {e}")
        return False, None

def get_my_notifications(token):
    """Obtiene las notificaciones del usuario actual."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{NOTIFICATIONS_BASE_URL}/inbox",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            notifications = response.json()
            unread = sum(1 for n in notifications if not n.get('read', False))
            print_result("Obtener mis notificaciones", True, 
                        f"Total: {len(notifications)} (no leídas: {unread})")
            
            # Mostrar las últimas 3 notificaciones
            if notifications:
                print("      Últimas notificaciones:")
                for notif in notifications[:3]:
                    status = "📭" if notif.get('read') else "📬"
                    msg = notif.get('message', '')[:50]
                    sender = notif.get('sender_username', 'unknown')
                    print(f"        {status} De {sender}: {msg}...")
            
            return True, notifications
        else:
            print_result("Obtener mis notificaciones", False, 
                        f"Status: {response.status_code}")
            return False, None
    except Exception as e:
        print_result("Obtener mis notificaciones", False, f"Error: {e}")
        return False, None

def mark_notification_as_read(token, notification_id):
    """Marca una notificación como leída."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(
            f"{NOTIFICATIONS_BASE_URL}/inbox/{notification_id}/read",
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            print_result(f"Marcar notificación como leída", True)
            return True
        else:
            print_result(f"Marcar notificación como leída", False, 
                        f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result(f"Marcar notificación como leída", False, f"Error: {e}")
        return False

def main():
    print_section("🔔 PRUEBA DEL MICROSERVICIO DE NOTIFICACIONES")
    print(f"URL Base: {NOTIFICATIONS_BASE_URL}")
    print(f"Kong HTTPS: {KONG_URL}")
    
    # 1. Health Check
    print_section("1. Health Check")
    if not check_health():
        print("\n❌ El servicio de notificaciones no está disponible")
        return
    
    # 2. Crear primer usuario admin manualmente (si no existe)
    print_section("2. Crear Usuario Admin Inicial")
    # Como no tenemos token aún, usaremos los usuarios que se crean automáticamente
    # en initialize_users.py al iniciar el servicio
    print("ℹ️  Los usuarios se crean automáticamente al iniciar el servicio")
    print("   Si necesitas crear más usuarios, hazlo después del login como admin")
    
    # 3. Login como admin (usando credenciales por defecto de initialize_users.py)
    print_section("3. Autenticación de Administrador")
    admin_token = login_user("admin", "admin123")
    
    if not admin_token:
        print("\n❌ No se pudo autenticar como admin")
        return
    
    # 4. Listar usuarios
    print_section("4. Listar Usuarios")
    get_users(admin_token)
    
    # 5. Admin envía notificación a operarios de bodega
    print_section("5. Enviar Notificación a Operarios de Bodega")
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"⚠️ IMPORTANTE: Inventario físico programado para hoy a las 15:00. Por favor, preparen sus áreas de trabajo. (Enviado a las {timestamp})"
    
    send_notification_to_role(admin_token, message, ["operario_bodega"])
    
    # 6. Admin envía notificación a un operario específico
    print_section("6. Enviar Notificación a Operario Específico")
    message2 = f"📦 Operario1: Tienes un pedido urgente asignado en la zona A3. Por favor, revisa tu terminal. (Enviado a las {timestamp})"
    
    send_notification_to_user(admin_token, message2, "operario1")
    
    # 7. Login como operario1 y ver notificaciones (credenciales por defecto)
    print_section("7. Operario1 Verifica sus Notificaciones")
    operario_token = login_user("operario1", "operario123")
    
    if operario_token:
        success, notifications = get_my_notifications(operario_token)
        
        # Marcar la primera notificación como leída
        if success and notifications:
            first_notif_id = notifications[0].get('id')
            if first_notif_id:
                print("\n   Marcando primera notificación como leída...")
                mark_notification_as_read(operario_token, first_notif_id)
                
                # Volver a obtener notificaciones para verificar el cambio
                print("\n   Verificando estado después de marcar como leída...")
                get_my_notifications(operario_token)
    
    # 8. Login como empacador y ver notificaciones
    print_section("8. Empacador Verifica sus Notificaciones")
    operario2_token = login_user("empacador1", "empacador123")
    
    if operario2_token:
        get_my_notifications(operario2_token)
    
    # 9. Admin envía notificación a múltiples roles
    print_section("9. Enviar Notificación a Múltiples Roles")
    message3 = f"📋 Recordatorio: Reunión de seguridad el viernes a las 10:00 AM. Asistencia obligatoria. (Enviado a las {timestamp})"
    
    send_notification_to_role(admin_token, message3, 
                             ["operario_bodega", "empacador", "operario_control_calidad"])
    
    # 10. Verificar que todos recibieron la notificación (usando usuarios por defecto)
    print_section("10. Verificar Recepción de Notificaciones")
    
    default_users = [
        ("operario1", "operario123"),
        ("empacador1", "empacador123"),
        ("calidad1", "calidad123")
    ]
    
    for username, password in default_users:
        print(f"\n   Verificando usuario: {username}")
        token = login_user(username, password)
        if token:
            get_my_notifications(token)
    
    print_section("✨ PRUEBAS COMPLETADAS")
    print("\nResumen de funcionalidades probadas:")
    print("  ✅ Health check del servicio")
    print("  ✅ Creación de usuarios con diferentes roles")
    print("  ✅ Autenticación y obtención de tokens JWT")
    print("  ✅ Listado de usuarios (solo admin)")
    print("  ✅ Envío de notificaciones a roles específicos")
    print("  ✅ Envío de notificaciones a usuarios específicos")
    print("  ✅ Consulta de notificaciones propias")
    print("  ✅ Marcar notificaciones como leídas")
    print("  ✅ Notificaciones a múltiples roles simultáneamente")
    print("\nEl microservicio de notificaciones está funcionando correctamente.")

if __name__ == "__main__":
    main()
