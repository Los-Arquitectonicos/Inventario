#!/usr/bin/env python3
"""
Generador de colección Postman con 50 productos distintos.
Este script crea un archivo JSON de Postman con 50 requests pre-configurados.
"""

import json
import random
from datetime import datetime

def generar_productos():
    """Genera una lista de 50 productos distintos"""
    
    marcas = [
        'Apple', 'Samsung', 'Sony', 'LG', 'Huawei', 'Xiaomi', 'OnePlus',
        'Google', 'Motorola', 'Nokia', 'Oppo', 'Vivo', 'Realme', 'Honor',
        'HP', 'Dell', 'Lenovo', 'Asus', 'Acer', 'MSI', 'Razer',
        'Microsoft', 'Canon', 'Nikon', 'GoPro', 'DJI', 'Bose', 'JBL',
        'Logitech', 'Corsair', 'SteelSeries', 'HyperX', 'Audio-Technica'
    ]
    
    categorias = [
        {
            'tipo': 'Smartphone',
            'modelos': ['Pro', 'Ultra', 'Max', 'Plus', 'Lite', 'Mini', 'Standard', 'Edge', 'Note', 'Galaxy'],
            'tallas': ['5.0"', '5.5"', '6.0"', '6.1"', '6.2"', '6.3"', '6.4"', '6.5"', '6.7"', '6.8"'],
            'peso_range': (0.15, 0.25),
            'precio_range': (200, 1500)
        },
        {
            'tipo': 'Laptop',
            'modelos': ['Pro', 'Gaming', 'Business', 'Ultra', 'Slim', 'Book', 'Air', 'Pavilion', 'Inspiron'],
            'tallas': ['11"', '12"', '13"', '14"', '15"', '15.6"', '16"', '17"', '17.3"'],
            'peso_range': (1.2, 2.8),
            'precio_range': (500, 3000)
        },
        {
            'tipo': 'Tablet',
            'modelos': ['Pro', 'Air', 'Mini', 'Plus', 'Standard', 'Kids', 'Gaming', 'Tab'],
            'tallas': ['7"', '8"', '9"', '10"', '10.1"', '10.5"', '11"', '12"', '12.9"'],
            'peso_range': (0.3, 0.8),
            'precio_range': (150, 1200)
        },
        {
            'tipo': 'Smartwatch',
            'modelos': ['Sport', 'Classic', 'Pro', 'Fitness', 'Ultra', 'SE', 'GT', 'Active', 'Watch'],
            'tallas': ['38mm', '40mm', '41mm', '42mm', '44mm', '45mm', '46mm', '49mm'],
            'peso_range': (0.03, 0.08),
            'precio_range': (100, 800)
        },
        {
            'tipo': 'Auriculares',
            'modelos': ['Pro', 'Sport', 'Studio', 'Wireless', 'Gaming', 'Noise Cancelling', 'Buds', 'AirPods'],
            'tallas': ['Over-ear', 'On-ear', 'In-ear', 'True Wireless', 'Neckband'],
            'peso_range': (0.05, 0.4),
            'precio_range': (50, 500)
        },
        {
            'tipo': 'Monitor',
            'modelos': ['Gaming', '4K', 'UltraWide', 'Curved', 'Professional', 'Portable', 'OLED'],
            'tallas': ['21"', '22"', '24"', '25"', '27"', '28"', '29"', '32"', '34"', '35"'],
            'peso_range': (3, 8),
            'precio_range': (200, 1500)
        },
        {
            'tipo': 'Teclado',
            'modelos': ['Mechanical', 'Gaming', 'Wireless', 'Compact', 'Ergonomic', 'RGB', 'Silent'],
            'tallas': ['60%', '65%', '75%', 'TKL', 'Full Size', 'Compact'],
            'peso_range': (0.5, 1.2),
            'precio_range': (30, 300)
        },
        {
            'tipo': 'Mouse',
            'modelos': ['Gaming', 'Wireless', 'Ergonomic', 'Vertical', 'Trackball', 'Precision', 'RGB'],
            'tallas': ['Standard', 'Mini', 'Large', 'XL'],
            'peso_range': (0.08, 0.15),
            'precio_range': (20, 150)
        }
    ]
    
    colores = [
        'Negro', 'Blanco', 'Gris', 'Plata', 'Dorado', 'Azul', 'Rojo',
        'Verde', 'Rosa', 'Morado', 'Naranja', 'Amarillo', 'Bronce',
        'Negro Mate', 'Azul Marino', 'Verde Militar', 'Rosa Gold',
        'Gris Espacial', 'Titanio', 'Champagne', 'Coral', 'Lavanda'
    ]
    
    caracteristicas = [
        'Alta calidad', 'Diseño premium', 'Tecnología avanzada', 'Rendimiento superior',
        'Batería de larga duración', 'Resistente al agua', 'Conectividad 5G',
        'Pantalla OLED', 'Procesador de última generación', 'Cámara profesional',
        'Audio de alta fidelidad', 'Diseño ergonómico', 'Construcción robusta',
        'Certificación IP68', 'Carga rápida', 'Memoria expandible'
    ]
    
    productos = []
    
    for i in range(50):
        categoria = random.choice(categorias)
        marca = random.choice(marcas)
        modelo = random.choice(categoria['modelos'])
        
        # Generar nombre único
        sufijo = random.choice(['', ' V2', ' Gen 2', f' {random.randint(2020, 2024)}', ' Edition', ' Series'])
        nombre = f"{marca} {categoria['tipo']} {modelo}{sufijo}"
        
        # Especificaciones
        peso = round(random.uniform(*categoria['peso_range']), 3)
        precio_base = random.uniform(*categoria['precio_range'])
        precio_costo = round(precio_base * random.uniform(0.6, 0.8), 2)
        precio_venta = round(precio_base * random.uniform(0.9, 1.4), 2)
        
        # Dimensiones realistas según categoría
        if categoria['tipo'] == 'Smartphone':
            dimensiones = f"{random.uniform(14, 17):.1f} x {random.uniform(7, 8):.1f} x {random.uniform(0.7, 1):.1f} cm"
        elif categoria['tipo'] == 'Laptop':
            dimensiones = f"{random.uniform(30, 40):.1f} x {random.uniform(20, 28):.1f} x {random.uniform(1.2, 2.5):.1f} cm"
        elif categoria['tipo'] == 'Tablet':
            dimensiones = f"{random.uniform(20, 28):.1f} x {random.uniform(15, 21):.1f} x {random.uniform(0.5, 1):.1f} cm"
        elif categoria['tipo'] == 'Smartwatch':
            dimensiones = f"{random.uniform(4, 5):.1f} x {random.uniform(4, 5):.1f} x {random.uniform(1, 1.5):.1f} cm"
        else:
            dimensiones = f"{random.uniform(10, 30):.1f} x {random.uniform(8, 20):.1f} x {random.uniform(2, 10):.1f} cm"
        
        # Descripción
        car1 = random.choice(caracteristicas)
        car2 = random.choice(caracteristicas)
        uso = random.choice(['profesional', 'personal', 'gaming', 'empresarial', 'educativo', 'creativo'])
        descripcion = f"{nombre} con {car1.lower()}. {car2} y diseño moderno. Ideal para uso {uso}."
        
        producto = {
            "nombre": nombre,
            "descripcion": descripcion,
            "marca": marca,
            "precio_costo": precio_costo,
            "precio_venta": precio_venta,
            "cantidad_stock": random.randint(5, 100),
            "peso": peso,
            "dimensiones": dimensiones,
            "color": random.choice(colores),
            "talla": random.choice(categoria['tallas'])
        }
        
        productos.append(producto)
    
    return productos

def crear_coleccion_postman(productos):
    """Crea la colección de Postman con los productos"""
    
    coleccion = {
        "info": {
            "name": "ProvesiWMS - 50 Productos Distintos",
            "description": f"Colección con 50 productos pre-configurados generada automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "base_url",
                "value": "http://127.0.0.1:8000",
                "type": "string"
            }
        ]
    }
    
    # Crear un request por cada producto
    for i, producto in enumerate(productos, 1):
        request_item = {
            "name": f"POST Producto {i:02d} - {producto['nombre']}",
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            "pm.test('Status code is 200', function () {",
                            "    pm.response.to.have.status(200);",
                            "});",
                            "",
                            "pm.test('Response has success field', function () {",
                            "    const jsonData = pm.response.json();",
                            "    pm.expect(jsonData).to.have.property('success');",
                            "    pm.expect(jsonData.success).to.be.true;",
                            "});",
                            "",
                            "pm.test('Product was created successfully', function () {",
                            "    const jsonData = pm.response.json();",
                            "    pm.expect(jsonData).to.have.property('producto');",
                            "    pm.expect(jsonData.producto).to.have.property('id');",
                            "});",
                            "",
                            f"console.log('✅ Producto {i}/50 creado: {producto['nombre']}');"
                        ],
                        "type": "text/javascript"
                    }
                }
            ],
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    },
                    {
                        "key": "Accept",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(producto, indent=2, ensure_ascii=False),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                },
                "url": {
                    "raw": "{{base_url}}/inventario/productos/crear/",
                    "host": ["{{base_url}}"],
                    "path": ["inventario", "productos", "crear", ""]
                }
            },
            "response": []
        }
        
        coleccion["item"].append(request_item)
    
    return coleccion

def main():
    """Función principal"""
    print("🏭 Generador de Colección Postman - 50 Productos Distintos")
    print("=" * 60)
    
    print("📦 Generando 50 productos distintos...")
    productos = generar_productos()
    
    print("🔧 Creando colección Postman...")
    coleccion = crear_coleccion_postman(productos)
    
    # Guardar archivo
    filename = "postman_50_productos_preconfigured.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(coleccion, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Colección creada: {filename}")
    print("\n📋 Productos generados:")
    print("-" * 60)
    
    for i, producto in enumerate(productos, 1):
        print(f"{i:2d}. {producto['nombre']}")
        print(f"    💰 ${producto['precio_venta']} | 📦 {producto['cantidad_stock']} units | 🎨 {producto['color']}")
    
    print("\n🚀 Instrucciones:")
    print("1. Importa el archivo en Postman")
    print("2. Asegúrate de que Django esté corriendo: python manage.py runserver")
    print("3. Ejecuta la colección completa con 'Run Collection'")
    print("4. ¡Verás 50 productos creados automáticamente!")

if __name__ == "__main__":
    main()