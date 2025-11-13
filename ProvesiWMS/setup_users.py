#!/usr/bin/env python
"""
Script para configurar usuarios iniciales de ProvesiWMS.
Ejecutar después del deployment para crear usuarios admin.
"""

import os
import sys
import django

# Cargar variables de entorno desde /etc/environment si no están disponibles
def load_environment_variables():
    try:
        with open('/etc/environment', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remover comillas si existen
                    value = value.strip('"').strip("'")
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        print("⚠️  /etc/environment no encontrado, usando variables actuales")

# Cargar variables de entorno
load_environment_variables()

# Verificar variables críticas
required_vars = ['DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
    print("💡 Ejecuta: source /etc/environment")
    sys.exit(1)

print(f"✅ Conectando a base de datos en: {os.environ.get('DATABASE_HOST')}")

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wms.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import call_command

from inventario.models import Usuario

def crear_usuario_admin():
    """Crea el usuario administrador inicial."""
    print("🔧 Configurando usuario administrador...")
    
    # Crear superuser de Django
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@provesi.com',
            password='ProvesiAdmin2024!',
            first_name='Administrador',
            last_name='Sistema'
        )
        print(f"✅ Superuser creado: {admin_user.username}")
    else:
        admin_user = User.objects.get(username='admin')
        print(f"ℹ️  Superuser ya existe: {admin_user.username}")
    
    # Crear usuario en el modelo de inventario
    if not Usuario.objects.filter(nombre_usuario='admin').exists():
        usuario_inventario = Usuario.objects.create(
            nombre_usuario='admin',
            email='admin@provesi.com',
            telefono='+57 300 123 4567',
            rol='admin'
        )
        print(f"✅ Usuario de inventario creado: {usuario_inventario.nombre_usuario} (rol: {usuario_inventario.rol})")
    else:
        print("ℹ️  Usuario de inventario ya existe")

def crear_usuario_gerente():
    """Crea un usuario gerente de ejemplo."""
    print("🔧 Configurando usuario gerente...")
    
    # Crear user de Django
    if not User.objects.filter(username='gerente').exists():
        gerente_user = User.objects.create_user(
            username='gerente',
            email='gerente@provesi.com',
            password='Gerente2024!',
            first_name='Juan Carlos',
            last_name='Rodríguez'
        )
        print(f"✅ Usuario Django creado: {gerente_user.username}")
    else:
        gerente_user = User.objects.get(username='gerente')
        print(f"ℹ️  Usuario Django ya existe: {gerente_user.username}")
    
    # Crear usuario en el modelo de inventario
    if not Usuario.objects.filter(nombre_usuario='gerente').exists():
        usuario_inventario = Usuario.objects.create(
            nombre_usuario='gerente',
            email='gerente@provesi.com',
            telefono='+57 301 234 5678',
            rol='gerente'
        )
        print(f"✅ Usuario de inventario creado: {usuario_inventario.nombre_usuario} (rol: {usuario_inventario.rol})")
    else:
        print("ℹ️  Usuario de inventario ya existe")

def crear_usuario_empleado():
    """Crea un usuario empleado de ejemplo."""
    print("🔧 Configurando usuario empleado...")
    
    # Crear user de Django
    if not User.objects.filter(username='empleado').exists():
        empleado_user = User.objects.create_user(
            username='empleado',
            email='empleado@provesi.com',
            password='Empleado2024!',
            first_name='María',
            last_name='García'
        )
        print(f"✅ Usuario Django creado: {empleado_user.username}")
    else:
        empleado_user = User.objects.get(username='empleado')
        print(f"ℹ️  Usuario Django ya existe: {empleado_user.username}")
    
    # Crear usuario en el modelo de inventario
    if not Usuario.objects.filter(nombre_usuario='empleado').exists():
        usuario_inventario = Usuario.objects.create(
            nombre_usuario='empleado',
            email='empleado@provesi.com',
            telefono='+57 302 345 6789',
            rol='empleado'
        )
        print(f"✅ Usuario de inventario creado: {usuario_inventario.nombre_usuario} (rol: {usuario_inventario.rol})")
    else:
        print("ℹ️  Usuario de inventario ya existe")

def main():
    print("🚀 Configurando ProvesiWMS - Sistema de Autenticación")
    print("=" * 50)
    
    try:
        # Crear migraciones si es necesario
        print("📊 Aplicando migraciones...")
        call_command('migrate', verbosity=0)
        print("✅ Migraciones aplicadas")
        
        # Crear usuarios
        crear_usuario_admin()
        crear_usuario_gerente()
        crear_usuario_empleado()
        
        print("\n" + "=" * 50)
        print("✅ Configuración completada exitosamente!")
        print("\n📋 INFORMACIÓN DE USUARIOS CREADOS:")
        print("   👨‍💼 Admin:    username=admin,    password=ProvesiAdmin2024!")
        print("   👨‍💼 Gerente:  username=gerente,  password=Gerente2024!")
        print("   👩‍💼 Empleado: username=empleado, password=Empleado2024!")
        print("\n🔐 ENDPOINTS DE AUTENTICACIÓN:")
        print("   POST /inventario/auth/login/")
        print("   POST /inventario/auth/logout/")
        print("   GET  /inventario/auth/profile/")
        print("   POST /inventario/auth/verify/")
        print("   POST /inventario/auth/change-password/")
        print("\n🌐 Para usar en AWS:")
        print("   1. Asegúrate que las librerías estén instaladas: pip install -r requirements.txt")
        print("   2. Configura las variables de entorno de la base de datos PostgreSQL")
        print("   3. Ejecuta: python manage.py migrate")
        print("   4. Ejecuta este script: python setup_users.py")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()