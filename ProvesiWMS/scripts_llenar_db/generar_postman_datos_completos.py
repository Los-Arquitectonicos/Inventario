"""
Genera coleccion Postman con todos los datos necesarios para pruebas de carga.

Crea:
- 50 productos
- 10 bodegas (diferentes ciudades)
- 100 ubicaciones por bodega (1,000 total, capacidad 1M cada una)

Uso:
    python generar_postman_datos_completos.py
"""

import json
import os
from decimal import Decimal


def generar_coleccion_completa():
    """Genera coleccion Postman con productos, bodegas y ubicaciones."""
    
    alb_url = "http://provesi-alb-1423351037.us-east-1.elb.amazonaws.com"
    base_url = f"{alb_url}/inventario"
    
    requests = []
    
    # 1. Productos (50 total)
    productos = [
        ("Laptop Dell XPS 13", "Laptop ultradelgada 13 pulgadas", "500000", "750000", "1.2", "30x21x2 cm", "Plateado", "13\"", "Dell"),
        ("Mouse Logitech MX Master", "Mouse inalambrico ergonomico", "50000", "75000", "0.14", "12x8x4 cm", "Negro", "Universal", "Logitech"),
        ("Teclado Mecanico Corsair", "Teclado mecanico RGB", "80000", "120000", "1.1", "44x13x4 cm", "Negro", "Full Size", "Corsair"),
        ("Monitor LG 27 4K", "Monitor 27 pulgadas 4K UHD", "300000", "450000", "5.5", "61x46x22 cm", "Negro", "27\"", "LG"),
        ("Audifonos Sony WH-1000XM4", "Audifonos con cancelacion de ruido", "200000", "300000", "0.25", "20x18x8 cm", "Negro", "Universal", "Sony"),
        ("Webcam Logitech C920", "Webcam Full HD 1080p", "60000", "90000", "0.16", "9x4x7 cm", "Negro", "Universal", "Logitech"),
        ("Disco SSD Samsung 1TB", "SSD NVMe 1TB alta velocidad", "80000", "120000", "0.008", "8x2x0.2 cm", "Negro", "M.2", "Samsung"),
        ("Memoria RAM Corsair 16GB", "RAM DDR4 3200MHz 16GB", "50000", "75000", "0.05", "13x3x0.1 cm", "Negro", "DDR4", "Corsair"),
        ("Router ASUS RT-AX88U", "Router WiFi 6 Gaming", "250000", "375000", "1.0", "30x18x6 cm", "Negro", "Universal", "ASUS"),
        ("Impresora HP LaserJet", "Impresora laser monocromatica", "180000", "270000", "7.0", "36x36x18 cm", "Gris", "Universal", "HP"),
    ]
    
    # Generar 50 productos variando los existentes
    for i in range(50):
        base_idx = i % len(productos)
        nombre, desc, costo, venta, peso, dim, color, talla, marca = productos[base_idx]
        
        # Variar el numero de producto
        nombre_final = f"{nombre} v{i+1}" if i >= len(productos) else nombre
        
        requests.append({
            "name": f"Producto {i+1}: {nombre_final}",
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "nombre": nombre_final,
                        "descripcion": desc,
                        "precio_costo": costo,
                        "precio_venta": venta,
                        "peso": peso,
                        "dimensiones": dim,
                        "color": color,
                        "talla": talla,
                        "marca": marca,
                        "cantidad_stock": 1000
                    }, indent=2)
                },
                "url": {
                    "raw": f"{base_url}/api/productos/",
                    "protocol": "http",
                    "host": base_url.replace("http://", "").split("/"),
                    "path": ["inventario", "api", "productos", ""]
                }
            },
            "response": []
        })
    
    # 2. Bodegas (10 total)
    ciudades = [
        ("Bogota", "Zona Industrial Norte"),
        ("Medellin", "Zona Industrial Sur"),
        ("Cali", "Parque Industrial"),
        ("Barranquilla", "Zona Franca"),
        ("Cartagena", "Puerto Industrial"),
        ("Bucaramanga", "Centro Logistico"),
        ("Pereira", "Zona Industrial"),
        ("Santa Marta", "Complejo Portuario"),
        ("Ibague", "Parque Empresarial"),
        ("Cucuta", "Zona Industrial Frontera")
    ]
    
    for i, (ciudad, direccion) in enumerate(ciudades, 1):
        requests.append({
            "name": f"Bodega {i}: {ciudad}",
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "nombre": f"Bodega {i}",
                        "ciudad": ciudad,
                        "direccion": direccion
                    }, indent=2)
                },
                "url": {
                    "raw": f"{base_url}/api/bodegas/",
                    "protocol": "http",
                    "host": base_url.replace("http://", "").split("/"),
                    "path": ["inventario", "api", "bodegas", ""]
                }
            },
            "response": []
        })
    
    # 3. Ubicaciones (100 por bodega = 1,000 total)
    pasillos = [chr(65 + j % 26) for j in range(26)]  # A-Z
    
    for bodega_num in range(1, 11):
        for j in range(100):
            pasillo = pasillos[j % len(pasillos)]
            estante = str((j // len(pasillos)) + 1)
            nivel = str((j % 5) + 1)
            
            requests.append({
                "name": f"B{bodega_num} Ubicacion {j+1}: {pasillo}-{estante}-{nivel}",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "bodega_id": bodega_num,
                            "pasillo": pasillo,
                            "estante": estante,
                            "nivel": nivel,
                            "capacidad_total": 1000000,
                            "capacidad_disponible": 1000000
                        }, indent=2)
                    },
                    "url": {
                        "raw": f"{base_url}/api/ubicaciones/",
                        "protocol": "http",
                        "host": base_url.replace("http://", "").split("/"),
                        "path": ["inventario", "api", "ubicaciones", ""]
                    }
                },
                "response": []
            })
    
    # Estructura de la coleccion
    coleccion = {
        "info": {
            "name": "ProvesiWMS - Datos Completos",
            "description": f"Crea todos los datos necesarios para pruebas de carga:\n\n"
                          f"- 50 productos\n"
                          f"- 10 bodegas\n"
                          f"- 1,000 ubicaciones (100 por bodega)\n"
                          f"- Capacidad total: 1,000,000,000 articulos",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": requests,
        "variable": [{"key": "base_url", "value": base_url}]
    }
    
    # Guardar archivo
    output_file = "postman_datos_completos.json"
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coleccion, f, indent=2, ensure_ascii=False)
    
    print(f"Coleccion generada: {output_file}")
    print(f"Total requests: {len(requests)}")
    print(f"  - Productos: 50")
    print(f"  - Bodegas: 10")
    print(f"  - Ubicaciones: 1,000")
    print(f"Tiempo estimado (100ms delay): ~{len(requests) * 0.1 / 60:.1f} minutos")
    
    return output_path


if __name__ == '__main__':
    generar_coleccion_completa()
