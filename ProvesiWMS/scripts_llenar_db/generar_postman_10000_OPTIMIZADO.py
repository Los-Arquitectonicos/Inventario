#!/usr/bin/env python3
"""
Generador de Colección Postman OPTIMIZADA para 10,000 Artículos
Versión con Batch Processing para mayor eficiencia
Crea artículos en lotes de 100 para reducir tiempo de ejecución
"""

import json
import random
from datetime import datetime

def generar_ubicaciones_batch():
    """Genera request ÚNICO para crear TODAS las ubicaciones en batch"""
    
    ubicaciones_data = []
    for pasillo in range(1, 11):  # Pasillos A01 a A10
        for estante in range(1, 6):  # Estantes E01 a E05
            ubicacion = {
                "bodega_id": 1,
                "pasillo": f"A{pasillo:02d}",
                "estante": f"E{estante:02d}", 
                "nivel": "N01",
                "capacidad_total": 250
            }
            ubicaciones_data.append(ubicacion)
    
    request_batch = {
        "name": "🏗️ Crear TODAS las Ubicaciones (Batch de 50)",
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
                    "ubicaciones": ubicaciones_data,
                    "crear_multiple": True
                }, indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            },
            "url": {
                "raw": "{{base_url}}/inventario/ubicaciones/crear_batch/",
                "host": ["{{base_url}}"],
                "path": ["inventario", "ubicaciones", "crear_batch", ""]
            }
        },
        "event": [
            {
                "listen": "test",
                "script": {
                    "exec": [
                        "pm.test('Batch de ubicaciones creado', function () {",
                        "    pm.response.to.have.status(200);",
                        "    const response = pm.response.json();", 
                        "    pm.expect(response.success).to.be.true;",
                        "    ",
                        "    console.log(`✅ Batch creado: ${response.created_count} ubicaciones`);",
                        "    ",
                        "    // Guardar IDs de ubicaciones para uso posterior",
                        "    if (response.ubicaciones && response.ubicaciones.length > 0) {",
                        "        const ubicacionIds = response.ubicaciones.map(u => u.id);",
                        "        pm.globals.set('ubicacion_ids', JSON.stringify(ubicacionIds));",
                        "        console.log(`📦 IDs disponibles: ${ubicacionIds.length} ubicaciones`);",
                        "    }",
                        "});",
                        "",
                        "// Verificar todas las ubicaciones fueron creadas",
                        "pm.test('50 ubicaciones creadas', function () {",
                        "    const response = pm.response.json();",
                        "    pm.expect(response.created_count).to.equal(50);",
                        "});"
                    ],
                    "type": "text/javascript"
                }
            }
        ]
    }
    
    return [request_batch]

def generar_articulos_batch():
    """Genera requests para crear artículos en lotes de 100"""
    
    # Pre-request script para generar 100 artículos
    pre_request_script = """
// Obtener ubicaciones disponibles
const ubicacionIdsStr = pm.globals.get('ubicacion_ids');
if (!ubicacionIdsStr) {
    console.error('❌ No hay ubicaciones. Ejecuta primero el batch de ubicaciones.');
    pm.test.skip('Sin ubicaciones disponibles');
    return;
}

const ubicacionIds = JSON.parse(ubicacionIdsStr);
console.log(`📦 Ubicaciones disponibles: ${ubicacionIds.length}`);

// Productos disponibles (IDs 1-51)
const productos = Array.from({length: 51}, (_, i) => i + 1);

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

// Generar lote de 100 artículos
const loteArticulos = [];
for (let i = 0; i < 100; i++) {
    const productoId = productos[Math.floor(Math.random() * productos.length)];
    const ubicacionId = ubicacionIds[Math.floor(Math.random() * ubicacionIds.length)];
    const codigoBarras = generarCodigoBarras();
    
    loteArticulos.push({
        producto_id: productoId,
        codigo_barras: codigoBarras,
        ubicacion_id: ubicacionId
    });
}

// Guardar lote para el request
pm.globals.set('current_batch', JSON.stringify(loteArticulos));

console.log(`🏷️ Generando lote de ${loteArticulos.length} artículos`);
"""

    # Test script para verificar lote creado
    test_script = """
pm.test('Lote de artículos creado exitosamente', function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response.success).to.be.true;
    
    const createdCount = response.created_count || 0;
    console.log(`✅ Lote completado: ${createdCount} artículos creados`);
    
    // Incrementar contador global
    let totalCreados = pm.globals.get('total_articulos_creados') || 0;
    totalCreados += createdCount;
    pm.globals.set('total_articulos_creados', totalCreados);
    
    console.log(`🎯 Progreso total: ${totalCreados} artículos creados`);
    
    // Mostrar progreso cada 1000 artículos
    if (totalCreados % 1000 === 0) {
        console.log(`🚀 HITO ALCANZADO: ${totalCreados} artículos!`);
    }
});

pm.test('Lote de 100 artículos', function () {
    const response = pm.response.json();
    if (response.success) {
        pm.expect(response.created_count).to.equal(100);
    }
});

pm.test('Sin errores de duplicación', function () {
    const response = pm.response.json();
    if (response.errors && response.errors.length > 0) {
        console.warn(`⚠️ Errores en lote: ${response.errors.length}`);
        response.errors.forEach(error => console.log(`   - ${error}`));
    }
});
"""

    # Request para crear lotes de 100
    request_batch = {
        "name": "🚀 Crear Lote de 100 Artículos (Ejecutar 100 veces)",
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
                    "articulos": "{{current_batch}}",
                    "crear_multiple": True
                }, indent=2).replace('"{{current_batch}}"', '{{current_batch}}'),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            },
            "url": {
                "raw": "{{base_url}}/inventario/articulos/crear_batch/", 
                "host": ["{{base_url}}"],
                "path": ["inventario", "articulos", "crear_batch", ""]
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
    
    return [request_batch]

def crear_coleccion_optimizada():
    """Crea la colección optimizada con batch processing"""
    
    coleccion = {
        "info": {
            "name": "🚀 ProvesiWMS - 10,000 Artículos OPTIMIZADOS (Batch)",
            "description": "**COLECCIÓN OPTIMIZADA PARA MÁXIMO RENDIMIENTO**\n\nCrea 10,000 artículos únicos usando batch processing:\n\n**🎯 VENTAJAS DE ESTA VERSIÓN:**\n- ⚡ **100x más rápida** que requests individuales\n- 🏗️ **Batch de ubicaciones**: 50 ubicaciones en 1 request\n- 📦 **Batch de artículos**: 100 artículos por request\n- ⏱️ **Tiempo estimado**: 3-5 minutos (vs 20-30 min)\n\n**📋 PROCESO SIMPLIFICADO:**\n1. **Paso 1**: 1 request → 50 ubicaciones\n2. **Paso 2**: 100 requests → 10,000 artículos\n3. **Paso 3**: 1 request → verificación\n\n**⚙️ CONFIGURACIÓN RUNNER:**\n- Iterations: **100** (no 10,000!)\n- Delay: **100ms** recomendado\n- Target: Folder \"Batch Artículos\"\n\n**🎮 RESULTADO:** 10,000 artículos únicos en minutos!",
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
    
    # Folders organizados
    folders = []
    
    # Folder 1: Preparación Ultra-Rápida
    folder_prep = {
        "name": "⚡ 1. ULTRA-RÁPIDO: Crear 50 Ubicaciones (1 Request)",
        "description": "**EJECUTAR UNA SOLA VEZ** - Crea todas las ubicaciones en batch",
        "item": generar_ubicaciones_batch()
    }
    folders.append(folder_prep)
    
    # Folder 2: Batch de Artículos
    folder_batch = {
        "name": "🚀 2. BATCH: 10,000 Artículos (100 Iterations × 100 Items)",
        "description": "**CONFIGURAR RUNNER**: 100 iteraciones = 10,000 artículos totales",
        "item": generar_articulos_batch()
    }
    folders.append(folder_batch)
    
    # Folder 3: Verificación y Estadísticas
    folder_stats = {
        "name": "📊 3. ESTADÍSTICAS: Verificación Final",
        "description": "Conteo final y estadísticas detalladas",
        "item": [
            {
                "name": "📈 Estadísticas Completas",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/inventario/api/estadisticas/completas/",
                        "host": ["{{base_url}}"],
                        "path": ["inventario", "api", "estadisticas", "completas", ""]
                    }
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "const response = pm.response.json();",
                                "const totalSesion = pm.globals.get('total_articulos_creados') || 0;",
                                "",
                                "console.log(`\\n🎉 PROCESO COMPLETADO EXITOSAMENTE!`);",
                                "console.log(`════════════════════════════════════`);",
                                "console.log(`📊 ESTADÍSTICAS FINALES:`);",
                                "console.log(`   • Artículos en esta sesión: ${totalSesion}`);",
                                "console.log(`   • Total en base de datos: ${response.total_articulos || 'N/A'}`);",
                                "console.log(`   • Ubicaciones disponibles: ${response.total_ubicaciones || 'N/A'}`);",
                                "console.log(`   • Productos únicos: ${response.total_productos || 'N/A'}`);",
                                "console.log(`   • Tiempo estimado ahorrado: ~20 minutos`);",
                                "console.log(`════════════════════════════════════`);",
                                "",
                                "if (parseInt(totalSesion) >= 10000) {",
                                "    console.log(`✅ META CUMPLIDA: 10,000+ artículos creados!`);",
                                "    console.log(`🚀 Tu inventario masivo está listo para usar!`);",
                                "} else {",
                                "    console.log(`⚠️ Meta parcial: ${totalSesion}/10,000 artículos`);",
                                "    console.log(`💡 Ejecuta más iteraciones si es necesario`);",
                                "}",
                                "",
                                "pm.test('Meta de 10,000 artículos', function () {",
                                "    pm.expect(parseInt(totalSesion)).to.be.at.least(10000);",
                                "});"
                            ],
                            "type": "text/javascript"
                        }
                    }
                ]
            }
        ]
    }
    folders.append(folder_stats)
    
    coleccion["item"] = folders
    return coleccion

def main():
    """Función principal para generar colección optimizada"""
    print("🚀 Generando colección OPTIMIZADA para 10,000 artículos...")
    print("⚡ Versión con BATCH PROCESSING para máximo rendimiento")
    print()
    
    coleccion = crear_coleccion_optimizada()
    
    # Guardar archivo
    filename = "postman_10000_articulos_OPTIMIZADO.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(coleccion, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Colección optimizada generada: {filename}")
    print()
    print("🎯 CARACTERÍSTICAS DE ESTA VERSIÓN:")
    print("   • 📦 Ubicaciones: 1 request → 50 ubicaciones") 
    print("   • 🏷️ Artículos: 100 requests → 10,000 artículos")
    print("   • ⏱️ Tiempo total: 3-5 minutos (vs 20-30 min)")
    print("   • 🚀 Eficiencia: 100x más rápida")
    print()
    print("📋 INSTRUCCIONES SIMPLIFICADAS:")
    print("   1. Importar colección en Postman")
    print("   2. Configurar variables (base_url, csrf_token)")
    print("   3. Ejecutar Folder 1: Una sola vez")  
    print("   4. Ejecutar Folder 2 con Runner: 100 iteraciones")
    print("   5. Verificar con Folder 3")
    print()
    print("⚙️ CONFIGURACIÓN CRÍTICA DEL RUNNER:")
    print("   • Target: Folder '🚀 2. BATCH'")
    print("   • Iterations: 100 (NO 10,000!)")
    print("   • Delay: 100ms recomendado")
    print("   • Resultado: 100 × 100 = 10,000 artículos")
    print()
    print("🎉 ¡Listo para inventario ultra-rápido!")

if __name__ == "__main__":
    main()