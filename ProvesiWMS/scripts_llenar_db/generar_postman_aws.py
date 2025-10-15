#!/usr/bin/env python3
"""
Generador de colección Postman para crear datos en AWS PostgreSQL.
Este script crea un archivo JSON de Postman pre-configurado para tu Load Balancer de AWS.
"""

import json
from datetime import datetime
from decimal import Decimal

def generar_datos_base():
    """Genera los datos base: 1 bodega, 1 ubicación, 50 productos"""
    
    datos = {
        "bodega": {
            "nombre": "Bodega Principal",
            "ciudad": "Bogota",
            "direccion": "Calle 100 #15-20, Bogotá"
        },
        "ubicacion": {
            "pasillo": "A",
            "estante": "1",
            "nivel": "1",
            "capacidad_total": 20000,
            "capacidad_disponible": 20000
        },
        "productos": []
    }
    
    # Generar 50 productos
    for i in range(1, 51):
        producto = {
            "nombre": f"Producto {i}",
            "descripcion": f"Descripción detallada del producto {i}. Ideal para pruebas de carga y demostración del sistema.",
            "marca": "Test Brand",
            "precio_costo": float(5 * i),
            "precio_venta": float(10 * i),
            "cantidad_stock": 1000,
            "peso": 0.5,
            "dimensiones": "10x10x10 cm",
            "color": "Azul",
            "talla": "M"
        }
        datos["productos"].append(producto)
    
    return datos

def crear_coleccion_postman(datos, alb_url):
    """Crea la colección de Postman con los requests necesarios"""
    
    # Limpiar URL (quitar /inventario/ si existe)
    base_url = alb_url.replace('/inventario/', '').rstrip('/')
    
    coleccion = {
        "info": {
            "name": "ProvesiWMS AWS - Crear Datos Base",
            "description": f"Colección para crear datos base en PostgreSQL AWS. Generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "base_url",
                "value": base_url,
                "type": "string"
            }
        ]
    }
    
    # 1. Request para crear bodega
    coleccion["item"].append({
        "name": "1️⃣ POST Bodega",
        "event": [{
            "listen": "test",
            "script": {
                "exec": [
                    "pm.test('Status code is 200 or 201', function () {",
                    "    pm.expect(pm.response.code).to.be.oneOf([200, 201]);",
                    "});",
                    "",
                    "console.log('✅ Bodega creada');"
                ],
                "type": "text/javascript"
            }
        }],
        "request": {
            "method": "POST",
            "header": [
                {"key": "Content-Type", "value": "application/json"}
            ],
            "body": {
                "mode": "raw",
                "raw": json.dumps(datos["bodega"], indent=2, ensure_ascii=False)
            },
            "url": {
                "raw": "{{base_url}}/inventario/bodegas/crear/",
                "host": ["{{base_url}}"],
                "path": ["inventario", "bodegas", "crear", ""]
            }
        }
    })
    
    # 2. Request para crear ubicación
    # Nota: Necesitarás ajustar el bodega_id manualmente después de crear la bodega
    ubicacion_con_bodega = datos["ubicacion"].copy()
    ubicacion_con_bodega["bodega_id"] = 1  # Asumiendo que es la primera bodega
    
    coleccion["item"].append({
        "name": "2️⃣ POST Ubicación (⚠️ Ajustar bodega_id)",
        "event": [{
            "listen": "test",
            "script": {
                "exec": [
                    "pm.test('Status code is 200 or 201', function () {",
                    "    pm.expect(pm.response.code).to.be.oneOf([200, 201]);",
                    "});",
                    "",
                    "console.log('✅ Ubicación creada');"
                ],
                "type": "text/javascript"
            }
        }],
        "request": {
            "method": "POST",
            "header": [
                {"key": "Content-Type", "value": "application/json"}
            ],
            "body": {
                "mode": "raw",
                "raw": json.dumps(ubicacion_con_bodega, indent=2, ensure_ascii=False)
            },
            "url": {
                "raw": "{{base_url}}/inventario/ubicaciones/crear/",
                "host": ["{{base_url}}"],
                "path": ["inventario", "ubicaciones", "crear", ""]
            }
        }
    })
    
    # 3. Requests para crear 50 productos
    for i, producto in enumerate(datos["productos"], 1):
        coleccion["item"].append({
            "name": f"3️⃣ POST Producto {i:02d} - {producto['nombre']}",
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Status code is 200 or 201', function () {",
                        "    pm.expect(pm.response.code).to.be.oneOf([200, 201]);",
                        "});",
                        "",
                        f"console.log('✅ Producto {i}/50 creado: {producto['nombre']}');"
                    ],
                    "type": "text/javascript"
                }
            }],
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"}
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(producto, indent=2, ensure_ascii=False)
                },
                "url": {
                    "raw": "{{base_url}}/inventario/productos/crear/",
                    "host": ["{{base_url}}"],
                    "path": ["inventario", "productos", "crear", ""]
                }
            }
        })
    
    return coleccion

def main():
    """Función principal"""
    print("=" * 80)
    print("🚀 GENERADOR DE COLECCIÓN POSTMAN PARA AWS")
    print("=" * 80)
    
    # URL de tu Load Balancer (puedes editarlo aquí)
    alb_url = "http://provesi-alb-1423351037.us-east-1.elb.amazonaws.com/inventario/"
    
    print(f"\n📡 URL configurada: {alb_url}")
    print("\n💡 Si necesitas cambiar la URL:")
    print("   1. Edita la variable 'alb_url' en este script, O")
    print("   2. Edita la variable {{base_url}} en Postman después de importar")
    
    print("\n📦 Generando datos base...")
    datos = generar_datos_base()
    
    print(f"   ✓ 1 bodega")
    print(f"   ✓ 1 ubicación (capacidad: 20,000)")
    print(f"   ✓ {len(datos['productos'])} productos")
    
    print("\n🔧 Creando colección Postman...")
    coleccion = crear_coleccion_postman(datos, alb_url)
    
    # Guardar archivo
    filename = "postman_aws_datos_base.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(coleccion, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Colección creada: {filename}")
    
    print("\n" + "=" * 80)
    print("📋 INSTRUCCIONES DE USO")
    print("=" * 80)
    
    print("""
1️⃣  IMPORTAR EN POSTMAN:
   - Abre Postman
   - Click en "Import"
   - Arrastra el archivo: postman_aws_datos_base.json
   - La colección aparecerá con 52 requests (1 bodega + 1 ubicación + 50 productos)

2️⃣  VERIFICAR URL:
   - Revisa la variable {{base_url}} en la colección
   - Debe apuntar a tu Load Balancer de AWS
   - Ejemplo: http://provesi-alb-xxxx.us-east-1.elb.amazonaws.com

3️⃣  EJECUTAR:
   - Click derecho en la colección
   - Selecciona "Run collection"
   - Configura:
     * Delay: 100ms (para no saturar el servidor)
     * Iterations: 1
   - Click "Run ProvesiWMS AWS"

4️⃣  VERIFICAR:
   - Abre en el navegador: http://[ALB_URL]/inventario/productos/
   - Deberías ver los 50 productos creados

⚠️  NOTA IMPORTANTE:
   Después de crear la bodega (request 1), puede que necesites ajustar el
   bodega_id en el request de ubicación. Verifica el ID en la respuesta del
   primer request.
""")
    
    print("=" * 80)
    print("✅ ¡Listo! Importa la colección en Postman y ejecuta.")
    print("=" * 80)

if __name__ == "__main__":
    main()
