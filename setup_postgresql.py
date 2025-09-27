#!/usr/bin/env python3
"""
Script de configuración inicial para PostgreSQL
Autor: Sistema de Inventario
Fecha: 2024
"""

import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

from django.db import connection
from django.core.management import execute_from_command_line
from dotenv import load_dotenv

def verificar_archivo_env():
    """Verificar que existe el archivo .env"""
    if not os.path.exists('.env'):
        print("⚠️  Archivo .env no encontrado. Creando desde .env.example...")
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Archivo .env creado. Por favor, edítalo con tus credenciales de PostgreSQL.")
            return False
        else:
            print("❌ No se encontró .env.example. Revisa la configuración.")
            return False
    return True

def verificar_conexion_postgresql():
    """Verificar conexión a PostgreSQL"""
    try:
        load_dotenv()
        print("🔍 Verificando conexión a PostgreSQL...")
        
        # Obtener configuración de base de datos
        db_name = os.getenv('DB_NAME', 'provesi_db')
        db_user = os.getenv('DB_USER', 'provesi_user')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        
        print(f"   📋 Base de datos: {db_name}")
        print(f"   👤 Usuario: {db_user}")
        print(f"   🌐 Host: {db_host}:{db_port}")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("✅ Conexión a PostgreSQL exitosa!")
                return True
                
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        print("\n💡 Posibles soluciones:")
        print("   1. Verificar que PostgreSQL esté corriendo")
        print("   2. Verificar credenciales en el archivo .env")
        print("   3. Verificar conectividad de red")
        print("   4. Verificar que la base de datos existe")
        return False

def ejecutar_migraciones():
    """Ejecutar migraciones de Django"""
    try:
        print("🔄 Ejecutando migraciones...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migraciones ejecutadas correctamente!")
        return True
    except Exception as e:
        print(f"❌ Error ejecutando migraciones: {e}")
        return False

def verificar_tablas():
    """Verificar que las tablas se crearon correctamente"""
    try:
        print("🔍 Verificando tablas creadas...")
        
        tablas_esperadas = [
            'inventario_categoria',
            'inventario_proveedor', 
            'inventario_producto',
            'inventario_bodega',
            'inventario_zonabodega',
            'inventario_articulo',
            'inventario_movimientoarticulo',
            'inventario_pedido',
            'inventario_detallepedido'
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'inventario_%'
                ORDER BY table_name
            """)
            
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
        print(f"   📊 Tablas encontradas: {len(tablas_existentes)}")
        
        tablas_faltantes = set(tablas_esperadas) - set(tablas_existentes)
        
        if tablas_faltantes:
            print(f"   ⚠️  Tablas faltantes: {tablas_faltantes}")
            return False
        else:
            print("   ✅ Todas las tablas del sistema están presentes")
            
            # Mostrar todas las tablas
            for tabla in sorted(tablas_existentes):
                print(f"      📋 {tabla}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False

def crear_datos_prueba():
    """Preguntar si crear datos de prueba"""
    respuesta = input("\n❓ ¿Deseas crear datos de prueba? (s/n): ").lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            print("🔄 Creando datos de prueba...")
            
            # Ejecutar script de datos de prueba
            script_path = project_dir / 'tests' / 'create_orders_test_data.py'
            if script_path.exists():
                exec(open(script_path).read())
                print("✅ Datos de prueba creados correctamente!")
            else:
                print("⚠️  Script de datos de prueba no encontrado")
                
        except Exception as e:
            print(f"❌ Error creando datos de prueba: {e}")
            
def mostrar_resumen():
    """Mostrar resumen final"""
    print("\n" + "="*60)
    print("🎉 CONFIGURACIÓN DE POSTGRESQL COMPLETADA")
    print("="*60)
    print("✅ Sistema configurado y listo para usar")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar el servidor: python manage.py runserver")
    print("   2. Probar las APIs en: http://localhost:8000/")
    print("   3. Revisar endpoints disponibles en PEDIDOS_README.md")
    print("\n🔧 Comandos útiles:")
    print("   • Crear superusuario: python manage.py createsuperuser")
    print("   • Acceder al admin: http://localhost:8000/admin/")
    print("   • Ejecutar tests: python tests/test_complete_api.py")

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN INICIAL DE POSTGRESQL")
    print("="*50)
    
    # Verificar archivo .env
    if not verificar_archivo_env():
        print("\n⏸️  Por favor, configura el archivo .env y ejecuta el script de nuevo.")
        return
    
    # Verificar conexión
    if not verificar_conexion_postgresql():
        print("\n⏸️  Configura la conexión a PostgreSQL y ejecuta el script de nuevo.")
        return
    
    # Ejecutar migraciones
    if not ejecutar_migraciones():
        print("\n❌ Error en las migraciones. Revisa los errores anteriores.")
        return
    
    # Verificar tablas
    if not verificar_tablas():
        print("\n❌ Error verificando las tablas. Revisa la configuración.")
        return
    
    # Crear datos de prueba
    crear_datos_prueba()
    
    # Mostrar resumen
    mostrar_resumen()

if __name__ == "__main__":
    main()