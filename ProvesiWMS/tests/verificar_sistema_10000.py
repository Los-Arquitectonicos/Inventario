#!/usr/bin/env python3
"""
Script de Verificación Rápida para Sistema de 10,000 Artículos
Verifica que todo esté listo antes de ejecutar Postman
"""

import os
import sys
import json

def verificar_archivos():
    """Verifica que todos los archivos necesarios existan"""
    archivos_necesarios = [
        'postman_10000_articulos_OPTIMIZADO.json',
        'generar_postman_10000_OPTIMIZADO.py', 
        'README_10000_ARTICULOS.md',
        'RESUMEN_10000_ARTICULOS.md'
    ]
    
    print("🔍 Verificando archivos necesarios...")
    faltantes = []
    
    for archivo in archivos_necesarios:
        if os.path.exists(archivo):
            size_kb = os.path.getsize(archivo) / 1024
            print(f"   ✅ {archivo} ({size_kb:.1f} KB)")
        else:
            print(f"   ❌ {archivo} - FALTANTE")
            faltantes.append(archivo)
    
    return len(faltantes) == 0

def verificar_coleccion():
    """Verifica que la colección Postman sea válida"""
    try:
        with open('postman_10000_articulos_OPTIMIZADO.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n📋 Verificando colección Postman...")
        
        # Verificar estructura básica
        if 'info' in data and 'item' in data:
            print(f"   ✅ Estructura válida")
            print(f"   ✅ Nombre: {data['info']['name']}")
            print(f"   ✅ Folders: {len(data['item'])}")
            
            # Contar requests totales
            total_requests = 0
            for folder in data['item']:
                if 'item' in folder:
                    total_requests += len(folder['item'])
            
            print(f"   ✅ Total requests: {total_requests}")
            return True
        else:
            print("   ❌ Estructura inválida")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def verificar_django():
    """Verifica configuración de Django"""
    print("\n🐍 Verificando Django...")
    
    try:
        # Verificar manage.py
        if os.path.exists('manage.py'):
            print("   ✅ manage.py encontrado")
        else:
            print("   ❌ manage.py no encontrado")
            return False
        
        # Verificar base de datos
        if os.path.exists('db.sqlite3'):
            size_mb = os.path.getsize('db.sqlite3') / (1024 * 1024)
            print(f"   ✅ Base de datos: {size_mb:.1f} MB")
        else:
            print("   ⚠️  Base de datos no encontrada")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def mostrar_instrucciones():
    """Muestra instrucciones finales"""
    print("\n" + "="*50)
    print("🚀 SISTEMA LISTO PARA USAR")
    print("="*50)
    print()
    print("📋 INSTRUCCIONES FINALES:")
    print()
    print("1️⃣  INICIAR DJANGO:")
    print("    python manage.py runserver")
    print()
    print("2️⃣  IMPORTAR EN POSTMAN:")
    print("    postman_10000_articulos_OPTIMIZADO.json")
    print()
    print("3️⃣  CONFIGURAR VARIABLES:")
    print("    base_url = http://127.0.0.1:8000") 
    print("    csrf_token = [obtener del formulario]")
    print()
    print("4️⃣  EJECUTAR EN ORDEN:")
    print("    • Folder 1: Una sola vez (50 ubicaciones)")
    print("    • Folder 2: Runner con 100 iteraciones (10,000 artículos)")
    print("    • Folder 3: Verificación final")
    print()
    print("⏱️  TIEMPO ESTIMADO: 3-5 minutos")
    print("🎯 RESULTADO: 10,000 artículos únicos")
    print()
    print("📖 DOCUMENTACIÓN COMPLETA:")
    print("    README_10000_ARTICULOS.md")
    print("    RESUMEN_10000_ARTICULOS.md")
    print()
    print("🎉 ¡BUEN INVENTARIO MASIVO!")

def main():
    print("🔧 Verificación del Sistema de 10,000 Artículos")
    print("=" * 50)
    
    # Verificaciones
    archivos_ok = verificar_archivos()
    coleccion_ok = verificar_coleccion() 
    django_ok = verificar_django()
    
    # Resultado final
    print(f"\n📊 RESUMEN DE VERIFICACIÓN:")
    print(f"   Archivos: {'✅ OK' if archivos_ok else '❌ FALTANTES'}")
    print(f"   Colección: {'✅ VÁLIDA' if coleccion_ok else '❌ INVÁLIDA'}")
    print(f"   Django: {'✅ LISTO' if django_ok else '❌ PROBLEMA'}")
    
    if archivos_ok and coleccion_ok and django_ok:
        print(f"\n🎉 SISTEMA COMPLETAMENTE LISTO")
        mostrar_instrucciones()
    else:
        print(f"\n⚠️  HAY PROBLEMAS - REVISAR ARRIBA")
        print(f"💡 Regenera los archivos si es necesario:")
        print(f"    python generar_postman_10000_OPTIMIZADO.py")

if __name__ == "__main__":
    main()