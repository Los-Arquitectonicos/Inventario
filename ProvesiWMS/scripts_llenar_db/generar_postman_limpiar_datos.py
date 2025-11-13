"""
Genera coleccion Postman para eliminar todos los datos de pruebas.

Elimina en orden:
1. Todos los articulos
2. Todas las ubicaciones en bodega
3. Todas las bodegas
4. Todos los productos

Uso:
    python generar_postman_limpiar_datos.py
"""

import json
import os


def generar_coleccion_limpieza():
    """Genera coleccion Postman para eliminar todos los datos."""
    
    alb_url = "https://provesi-alb-2003818714.us-east-1.elb.amazonaws.com"
    base_url = f"{alb_url}/inventario"
    
    requests = []
    
    # Nota: Estos endpoints deben implementarse en el backend
    # Por ahora, documentamos la estructura esperada
    
    requests.append({
        "name": "1. Eliminar todos los articulos",
        "request": {
            "method": "DELETE",
            "header": [],
            "url": {
                "raw": f"{base_url}/api/articulos/eliminar_todos/",
                "protocol": "http",
                "host": [alb_url.replace("http://", "")],
                "path": ["inventario", "api", "articulos", "eliminar_todos", ""]
            }
        },
        "response": []
    })
    
    requests.append({
        "name": "2. Eliminar todas las ubicaciones",
        "request": {
            "method": "DELETE",
            "header": [],
            "url": {
                "raw": f"{base_url}/api/ubicaciones/eliminar_todas/",
                "protocol": "http",
                "host": [alb_url.replace("http://", "")],
                "path": ["inventario", "api", "ubicaciones", "eliminar_todas", ""]
            }
        },
        "response": []
    })
    
    requests.append({
        "name": "3. Eliminar todas las bodegas",
        "request": {
            "method": "DELETE",
            "header": [],
            "url": {
                "raw": f"{base_url}/api/bodegas/eliminar_todas/",
                "protocol": "http",
                "host": [alb_url.replace("http://", "")],
                "path": ["inventario", "api", "bodegas", "eliminar_todas", ""]
            }
        },
        "response": []
    })
    
    requests.append({
        "name": "4. Eliminar todos los productos",
        "request": {
            "method": "DELETE",
            "header": [],
            "url": {
                "raw": f"{base_url}/api/productos/eliminar_todos/",
                "protocol": "http",
                "host": [alb_url.replace("http://", "")],
                "path": ["inventario", "api", "productos", "eliminar_todos", ""]
            }
        },
        "response": []
    })
    
    # Estructura de la coleccion
    coleccion = {
        "info": {
            "name": "ProvesiWMS - Limpiar Datos",
            "description": "Elimina todos los datos de pruebas en orden correcto:\n\n"
                          "1. Articulos\n"
                          "2. Ubicaciones\n"
                          "3. Bodegas\n"
                          "4. Productos\n\n"
                          "NOTA: Requiere endpoints de eliminacion masiva en el backend.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": requests,
        "variable": [{"key": "base_url", "value": base_url}]
    }
    
    # Guardar archivo
    output_file = "postman_limpiar_datos.json"
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coleccion, f, indent=2, ensure_ascii=False)
    
    print(f"Coleccion generada: {output_file}")
    print(f"Total requests: {len(requests)}")
    print(f"\nNOTA: Requiere implementar endpoints de eliminacion masiva en el backend:")
    print(f"  - DELETE /api/articulos/eliminar_todos/")
    print(f"  - DELETE /api/ubicaciones/eliminar_todas/")
    print(f"  - DELETE /api/bodegas/eliminar_todas/")
    print(f"  - DELETE /api/productos/eliminar_todos/")
    
    return output_path


if __name__ == '__main__':
    generar_coleccion_limpieza()
