#!/usr/bin/env python3
"""
Script simple para crear usuario administrador en ProvesiWMS.
Ejecutar desde el directorio ProvesiWMS en la instancia EC2.

Uso:
    python3 crear_admin.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from inventario.models import Usuario

def crear_admin():
    """Crea usuario admin si no existe."""
    
    username = "admin"
    password = "admin123"
    email = "admin@provesiwms.com"
    
    # Verificar si ya existe
    if Usuario.objects.filter(username=username).exists():
        print(f"✅ El usuario '{username}' ya existe")
        usuario = Usuario.objects.get(username=username)
        print(f"   - ID: {usuario.id}")
        print(f"   - Rol: {usuario.rol}")
        print(f"   - Email: {usuario.email}")
        return usuario
    
    # Crear nuevo usuario
    print(f"🔨 Creando usuario '{username}'...")
    
    usuario = Usuario.objects.create(
        username=username,
        email=email,
        nombre_completo="Administrador del Sistema",
        rol="admin",
        departamento="TI",
        telefono="3001234567",
        activo=True
    )
    
    # Establecer contraseña
    usuario.set_password(password)
    usuario.save()
    
    print(f"✅ Usuario creado exitosamente!")
    print(f"   - Username: {username}")
    print(f"   - Password: {password}")
    print(f"   - Email: {email}")
    print(f"   - Rol: {usuario.rol}")
    print(f"   - ID: {usuario.id}")
    
    return usuario

def crear_usuarios_adicionales():
    """Crea usuarios adicionales para pruebas."""
    
    usuarios = [
        {
            "username": "gerente",
            "password": "gerente123",
            "email": "gerente@provesiwms.com",
            "nombre_completo": "Gerente de Operaciones",
            "rol": "gerente",
            "departamento": "Operaciones"
        },
        {
            "username": "supervisor",
            "password": "supervisor123",
            "email": "supervisor@provesiwms.com",
            "nombre_completo": "Supervisor de Bodega",
            "rol": "supervisor",
            "departamento": "Bodega"
        },
        {
            "username": "operador",
            "password": "operador123",
            "email": "operador@provesiwms.com",
            "nombre_completo": "Operador de Bodega",
            "rol": "operador",
            "departamento": "Bodega"
        }
    ]
    
    print("\n🔨 Creando usuarios adicionales...")
    
    for user_data in usuarios:
        username = user_data["username"]
        
        if Usuario.objects.filter(username=username).exists():
            print(f"   ⚠️  Usuario '{username}' ya existe, omitiendo...")
            continue
        
        usuario = Usuario.objects.create(
            username=username,
            email=user_data["email"],
            nombre_completo=user_data["nombre_completo"],
            rol=user_data["rol"],
            departamento=user_data["departamento"],
            telefono="3009876543",
            activo=True
        )
        
        usuario.set_password(user_data["password"])
        usuario.save()
        
        print(f"   ✅ Usuario '{username}' creado (rol: {user_data['rol']})")
    
    print("\n✅ Proceso completado!")
    print("\n📋 Resumen de usuarios:")
    for usuario in Usuario.objects.all().order_by('rol'):
        print(f"   - {usuario.username:15} | {usuario.rol:12} | {usuario.email}")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("PROVESI WMS - Configuración de Usuarios")
        print("=" * 60)
        print()
        
        # Crear admin
        crear_admin()
        
        # Preguntar si crear usuarios adicionales
        print("\n¿Crear usuarios adicionales? (gerente, supervisor, operador)")
        respuesta = input("Presiona Enter para continuar o 'n' para omitir: ")
        
        if respuesta.lower() != 'n':
            crear_usuarios_adicionales()
        else:
            print("\n✅ Solo se creó el usuario admin")
        
        print("\n" + "=" * 60)
        print("Configuración completada exitosamente!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
