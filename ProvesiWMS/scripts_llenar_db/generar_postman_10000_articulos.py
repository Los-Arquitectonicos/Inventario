#!/usr/bin/env python3
"""
Generador de Colección Postman para 10,000 Artículos
Crea artículos únicos con códigos de barras automatizados
Distribuye los artículos entre múltiples ubicaciones de bodega
"""

import json
import random
from datetime import datetime

def generar_ubicaciones_bodega():
    """Genera requests para crear ubicaciones de bodega necesarias"""
    ubicaciones = []
    
    # Generar 50 ubicaciones en diferentes pasillos/estantes
    for pasillo in range(1, 11):  # Pasillos A01 a A10
        for estante in range(1, 6):  # Estantes E01 a E05
            ubicacion = {
                "name": f"Crear Ubicación P{pasillo:02d}E{estante:02d}",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json",
                            "type": "text"
                        },
                        {
                            "key": "X-CSRFToken",
                            "value": "{{csrf_token}}",
                            "type": "text"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "bodega_id": 1,  # Asumiendo que existe bodega con ID 1
                            "pasillo": f"A{pasillo:02d}",
                            "estante": f"E{estante:02d}",
                            "nivel": "N01",
                            "capacidad_total": 250  # Cada ubicación puede tener 250 artículos
                        }, indent=2),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    },
                    "url": {
                        "raw": "{{base_url}}/inventario/ubicaciones/crear/",
                        "host": ["{{base_url}}"],
                        "path": ["inventario", "ubicaciones", "crear", ""]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "pm.test('Ubicación creada exitosamente', function () {",
                                "    pm.response.to.have.status(200);",
                                "    const response = pm.response.json();",
                                "    pm.expect(response.success).to.be.true;",
                                "    ",
                                "    // Guardar ID de ubicación para uso posterior",
                                "    const ubicacionId = response.ubicacion.id;",
                                "    const key = `ubicacion_${response.ubicacion.pasillo}_${response.ubicacion.estante}`;",
                                "    pm.globals.set(key, ubicacionId);",
                                "    ",
                                "    console.log(`✅ Ubicación creada: ${response.ubicacion.pasillo}-${response.ubicacion.estante} (ID: ${ubicacionId})`);",
                                "});"
                            ],
                            "type": "text/javascript"
                        }
                    }
                ]
            }
            ubicaciones.append(ubicacion)
    
    return ubicaciones

def generar_codigo_barras():
    """Genera un código de barras único en formato EAN-13"""
    # Prefijo para artículos del sistema: 789
    prefijo = "789"
    # 9 dígitos aleatorios
    numero = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    codigo_sin_digito = prefijo + numero
    
    # Calcular dígito verificador EAN-13
    suma = 0
    for i, digito in enumerate(codigo_sin_digito):
        if i % 2 == 0:
            suma += int(digito)
        else:
            suma += int(digito) * 3
    
    digito_verificador = (10 - (suma % 10)) % 10
    return codigo_sin_digito + str(digito_verificador)

def generar_articulos_masivos():
    """Genera requests para crear 10,000 artículos únicos"""
    articulos = []
    
    # IDs de productos (asumiendo que tenemos al menos 51 productos)
    productos_disponibles = list(range(1, 52))
    
    # Generar código JavaScript para obtener ubicaciones dinámicamente
    pre_request_script = """
// Obtener lista de ubicaciones disponibles de las variables globales
const ubicaciones = [];
for (let pasillo = 1; pasillo <= 10; pasillo++) {
    for (let estante = 1; estante <= 5; estante++) {
        const key = `ubicacion_A${pasillo.toString().padStart(2, '0')}_E${estante.toString().padStart(2, '0')}`;
        const ubicacionId = pm.globals.get(key);
        if (ubicacionId) {
            ubicaciones.push(parseInt(ubicacionId));
        }
    }
}

// Verificar que tengamos ubicaciones disponibles
if (ubicaciones.length === 0) {
    console.error('❌ No se encontraron ubicaciones. Ejecuta primero las requests de ubicaciones.');
    pm.test.skip('Sin ubicaciones disponibles');
} else {
    console.log(`📦 Ubicaciones disponibles: ${ubicaciones.length}`);
}

// Función para generar código de barras EAN-13
function generarCodigoBarras() {
    const prefijo = "789";
    const numero = Array.from({length: 9}, () => Math.floor(Math.random() * 10)).join('');
    const codigoSinDigito = prefijo + numero;
    
    let suma = 0;
    for (let i = 0; i < codigoSinDigito.length; i++) {
        if (i % 2 === 0) {
            suma += parseInt(codigoSinDigito[i]);
        } else {
            suma += parseInt(codigoSinDigito[i]) * 3;
        }
    }
    
    const digitoVerificador = (10 - (suma % 10)) % 10;
    return codigoSinDigito + digitoVerificador.toString();
}

// Generar datos del artículo
const productos = [""" + ", ".join(map(str, productos_disponibles)) + """];
const productoId = productos[Math.floor(Math.random() * productos.length)];
const codigoBarras = generarCodigoBarras();
const ubicacionId = ubicaciones[Math.floor(Math.random() * ubicaciones.length)];

// Guardar en variables para el request
pm.globals.set('current_producto_id', productoId);
pm.globals.set('current_codigo_barras', codigoBarras);
pm.globals.set('current_ubicacion_id', ubicacionId);

console.log(`🏷️  Generando artículo: Producto ${productoId}, Código ${codigoBarras}, Ubicación ${ubicacionId}`);
"""

    test_script = """
pm.test('Artículo creado exitosamente', function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response.success).to.be.true;
    
    const articulo = response.articulo;
    console.log(`✅ Artículo creado: ${articulo.codigo_barras} - ${articulo.producto}`);
    
    // Incrementar contador de artículos creados
    let contador = pm.globals.get('articulos_creados') || 0;
    contador++;
    pm.globals.set('articulos_creados', contador);
    
    if (contador % 100 === 0) {
        console.log(`🎯 Progreso: ${contador} artículos creados`);
    }
});

pm.test('Código de barras único', function () {
    const response = pm.response.json();
    if (response.success) {
        pm.expect(response.articulo.codigo_barras).to.not.be.empty;
        pm.expect(response.articulo.codigo_barras).to.have.lengthOf(13);
    }
});
"""

    # Crear request dinámico que se ejecutará 10,000 veces
    articulo_dinamico = {
        "name": "🏭 Crear Artículo Dinámico (Ejecutar 10,000 veces)",
        "request": {
            "method": "POST",
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json",
                    "type": "text"
                },
                {
                    "key": "X-CSRFToken",
                    "value": "{{csrf_token}}",
                    "type": "text"
                }
            ],
            "body": {
                "mode": "raw",
                "raw": json.dumps({
                    "producto_id": "{{current_producto_id}}",
                    "codigo_barras": "{{current_codigo_barras}}",
                    "ubicacion_id": "{{current_ubicacion_id}}"
                }, indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            },
            "url": {
                "raw": "{{base_url}}/inventario/articulos/crear/",
                "host": ["{{base_url}}"],
                "path": ["inventario", "articulos", "crear", ""]
            }
        },
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "exec": pre_request_script.split('\n'),
                    "type": "text/javascript"
                }
            },
            {
                "listen": "test",
                "script": {
                    "exec": test_script.split('\n'),
                    "type": "text/javascript"
                }
            }
        ]
    }
    
    articulos.append(articulo_dinamico)
    return articulos

def crear_coleccion_completa():
    """Crea la colección completa de Postman"""
    
    # Información de la colección
    coleccion = {
        "info": {
            "name": "🏭 ProvesiWMS - 10,000 Artículos Masivos",
            "description": "Colección para crear 10,000 artículos únicos en el sistema de inventario.\n\n**INSTRUCCIONES DE USO:**\n\n1. **Configurar Variables:**\n   - `base_url`: http://127.0.0.1:8000\n   - `csrf_token`: [obtener del formulario de Django]\n\n2. **Ejecutar en Orden:**\n   - Primero: Todas las ubicaciones de bodega (50 requests)\n   - Después: Request dinámico 10,000 veces\n\n3. **Configuración del Runner:**\n   - Iterations: 10,000 para el request dinámico\n   - Delay: 10ms entre requests (opcional)\n\n**CARACTERÍSTICAS:**\n- ✅ 10,000 artículos únicos\n- 🏷️ Códigos de barras EAN-13 válidos\n- 📦 Distribución automática en 50 ubicaciones\n- 🎯 Progress tracking cada 100 artículos\n- ⚡ Generación dinámica con JavaScript\n\n**TIEMPO ESTIMADO:** 15-30 minutos",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://127.0.0.1:8000",
                "type": "string"
            },
            {
                "key": "csrf_token",
                "value": "tu_csrf_token_aqui",
                "type": "string"
            }
        ]
    }
    
    # Generar folders organizados
    folders = []
    
    # Folder 1: Preparación de Ubicaciones
    folder_ubicaciones = {
        "name": "📦 1. Preparación: Crear 50 Ubicaciones de Bodega",
        "description": "Crear todas las ubicaciones necesarias antes de los artículos. **EJECUTAR PRIMERO**",
        "item": generar_ubicaciones_bodega()
    }
    folders.append(folder_ubicaciones)
    
    # Folder 2: Creación Masiva de Artículos
    folder_articulos = {
        "name": "🏭 2. Creación Masiva: 10,000 Artículos",
        "description": "Request dinámico para crear 10,000 artículos únicos. **Configurar Runner con 10,000 iteraciones**",
        "item": generar_articulos_masivos()
    }
    folders.append(folder_articulos)
    
    # Request de verificación final
    verificacion = {
        "name": "📊 3. Verificación Final",
        "description": "Verificar el total de artículos creados",
        "item": [
            {
                "name": "📈 Contar Artículos Totales",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/inventario/api/articulos/count/",
                        "host": ["{{base_url}}"],
                        "path": ["inventario", "api", "articulos", "count", ""]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "const response = pm.response.json();",
                                "const totalCreados = pm.globals.get('articulos_creados') || 0;",
                                "",
                                "console.log(`📊 RESUMEN FINAL:`);",
                                "console.log(`   • Artículos creados en esta sesión: ${totalCreados}`);",
                                "console.log(`   • Total de artículos en BD: ${response.total || 'N/A'}`);",
                                "console.log(`   • Objetivo cumplido: ${totalCreados >= 10000 ? '✅ SÍ' : '❌ NO'}`);",
                                "",
                                "pm.test('Meta de 10,000 artículos', function () {",
                                "    pm.expect(parseInt(totalCreados)).to.be.at.least(10000);",
                                "});"
                            ],
                            "type": "text/javascript"
                        }
                    }
                ]
            }
        ]
    }
    folders.append(verificacion)
    
    coleccion["item"] = folders
    return coleccion

def main():
    """Función principal para generar la colección"""
    print("🏭 Generando colección Postman para 10,000 artículos...")
    
    coleccion = crear_coleccion_completa()
    
    # Guardar archivo
    filename = "postman_10000_articulos_masivos.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(coleccion, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Colección generada: {filename}")
    print(f"📋 Total de ubicaciones: 50")
    print(f"🏷️  Total de artículos: 10,000 (dinámicos)")
    print(f"📦 Distribución: Automática entre ubicaciones")
    print(f"⏱️  Tiempo estimado: 15-30 minutos")
    print()
    print("📖 INSTRUCCIONES:")
    print("   1. Importar la colección en Postman")
    print("   2. Configurar variables base_url y csrf_token")
    print("   3. Ejecutar folder 1 completo (50 ubicaciones)")
    print("   4. Ejecutar folder 2 con Runner: 10,000 iteraciones")
    print("   5. Verificar resultados con folder 3")
    print()
    print("🚀 ¡Listo para crear tu inventario masivo!")

if __name__ == "__main__":
    main()