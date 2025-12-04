"""
AWS Lambda - Generador de Reportes de Inventario ProvesiWMS
Envía reportes periódicos al microservicio de notificaciones.
"""

import os
import json
import urllib.request
import urllib.error
import psycopg2
from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================

DB_CONFIG = {
    "host": os.environ.get("DATABASE_HOST", "localhost"),
    "port": os.environ.get("DATABASE_PORT", "5432"),
    "database": os.environ.get("DATABASE_NAME", "provesi_wms"),
    "user": os.environ.get("DATABASE_USER", "provesi_user"),
    "password": os.environ.get("DATABASE_PASSWORD", "provesi_password_2024"),
}

NOTIFICATIONS_URL = os.environ.get("NOTIFICATIONS_URL", "http://localhost:8001")
NOTIFICATIONS_USER = os.environ.get("NOTIFICATIONS_USER", "admin")
NOTIFICATIONS_PASSWORD = os.environ.get("NOTIFICATIONS_PASSWORD", "admin123")


# ============================================================
# FUNCIONES DE RECOPILACIÓN DE DATOS
# ============================================================

def get_db_connection():
    """Conectar a la base de datos PostgreSQL."""
    # Map DB_CONFIG explicitly to psycopg2.connect parameters to satisfy type checkers
    port_str = DB_CONFIG.get("port")
    port = int(port_str) if port_str is not None and port_str != "" else None
    return psycopg2.connect(
        host=DB_CONFIG.get("host"),
        port=port,
        dbname=DB_CONFIG.get("database"),
        user=DB_CONFIG.get("user"),
        password=DB_CONFIG.get("password"),
    )


def get_total_productos(cursor):
    """Obtener total de productos."""
    cursor.execute("SELECT COUNT(*) FROM inventario_producto")
    return cursor.fetchone()[0]


def get_productos_sin_stock(cursor):
    """Obtener productos sin stock."""
    cursor.execute("""
        SELECT nombre, sku, cantidad_stock 
        FROM inventario_producto 
        WHERE cantidad_stock = 0
    """)
    return cursor.fetchall()


def get_productos_bajo_stock(cursor, umbral=10):
    """Obtener productos con stock bajo."""
    cursor.execute("""
        SELECT nombre, sku, cantidad_stock 
        FROM inventario_producto 
        WHERE cantidad_stock > 0 AND cantidad_stock <= %s
        ORDER BY cantidad_stock ASC
    """, (umbral,))
    return cursor.fetchall()


def get_total_bodegas(cursor):
    """Obtener total de bodegas."""
    cursor.execute("SELECT COUNT(*) FROM inventario_bodega")
    return cursor.fetchone()[0]


def get_pedidos_por_estado(cursor):
    """Obtener conteo de pedidos por estado."""
    cursor.execute("""
        SELECT estado, COUNT(*) 
        FROM inventario_pedido 
        GROUP BY estado
    """)
    return dict(cursor.fetchall())


def get_valor_total_inventario(cursor):
    """Obtener valor total del inventario."""
    cursor.execute("""
        SELECT COALESCE(SUM(precio * cantidad_stock), 0) 
        FROM inventario_producto
    """)
    return float(cursor.fetchone()[0])


# ============================================================
# FUNCIÓN DE GENERACIÓN DE REPORTE
# ============================================================

def generar_reporte():
    """Recopilar datos y generar el reporte de inventario."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Recopilar datos
        total_productos = get_total_productos(cursor)
        productos_sin_stock = get_productos_sin_stock(cursor)
        productos_bajo_stock = get_productos_bajo_stock(cursor)
        total_bodegas = get_total_bodegas(cursor)
        pedidos_por_estado = get_pedidos_por_estado(cursor)
        valor_inventario = get_valor_total_inventario(cursor)
        
        # Construir mensaje del reporte
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        reporte = f"""
📊 REPORTE DE INVENTARIO PROVESIWMS
📅 Fecha: {fecha}
{'='*40}

📦 RESUMEN GENERAL
   • Total productos: {total_productos}
   • Total bodegas: {total_bodegas}
   • Valor del inventario: ${valor_inventario:,.2f}

⚠️ ALERTAS DE STOCK
   • Productos sin stock: {len(productos_sin_stock)}
   • Productos con bajo stock: {len(productos_bajo_stock)}
"""
        
        if productos_sin_stock:
            reporte += "\n🔴 PRODUCTOS SIN STOCK:\n"
            for nombre, sku, _ in productos_sin_stock[:5]:
                reporte += f"   • {nombre} (SKU: {sku})\n"
            if len(productos_sin_stock) > 5:
                reporte += f"   ... y {len(productos_sin_stock) - 5} más\n"
        
        if productos_bajo_stock:
            reporte += "\n🟡 PRODUCTOS CON BAJO STOCK:\n"
            for nombre, sku, cantidad in productos_bajo_stock[:5]:
                reporte += f"   • {nombre} (SKU: {sku}) - {cantidad} unidades\n"
            if len(productos_bajo_stock) > 5:
                reporte += f"   ... y {len(productos_bajo_stock) - 5} más\n"
        
        if pedidos_por_estado:
            reporte += "\n📋 PEDIDOS POR ESTADO:\n"
            for estado, cantidad in pedidos_por_estado.items():
                emoji = {"pendiente": "🕐", "preparando": "📦", "enviado": "🚚", 
                        "entregado": "✅", "cancelado": "❌"}.get(estado, "📌")
                reporte += f"   {emoji} {estado.capitalize()}: {cantidad}\n"
        
        reporte += f"\n{'='*40}\n🤖 Reporte generado automáticamente por Lambda"
        
        return reporte
        
    finally:
        cursor.close()
        conn.close()


# ============================================================
# FUNCIÓN DE ENVÍO DE NOTIFICACIÓN
# ============================================================

def obtener_token_notificaciones():
    """Autenticar con el servicio de notificaciones."""
    url = f"{NOTIFICATIONS_URL}/auth/login"
    data = json.dumps({
        "username": NOTIFICATIONS_USER,
        "password": NOTIFICATIONS_PASSWORD
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get("access_token")
    except urllib.error.URLError as e:
        print(f"Error autenticando: {e}")
        return None


def enviar_notificacion(mensaje, token):
    """Enviar notificación a usuarios con rol admin."""
    url = f"{NOTIFICATIONS_URL}/notifications/send"
    data = json.dumps({
        "message": mensaje,
        "roles": ["admin"]  # Solo administradores reciben el reporte
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except urllib.error.URLError as e:
        print(f"Error enviando notificación: {e}")
        return False


# ============================================================
# HANDLER LAMBDA
# ============================================================

def lambda_handler(event, context):
    """Handler principal de AWS Lambda."""
    print("Iniciando generación de reporte de inventario...")
    
    try:
        # Generar reporte
        reporte = generar_reporte()
        print("Reporte generado exitosamente")
        
        # Obtener token de autenticación
        token = obtener_token_notificaciones()
        if not token:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "No se pudo autenticar con notificaciones"})
            }
        
        # Enviar notificación
        exito = enviar_notificacion(reporte, token)
        
        if exito:
            print("Notificación enviada exitosamente")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Reporte enviado exitosamente"})
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Error enviando notificación"})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# Para pruebas locales
if __name__ == "__main__":
    resultado = lambda_handler({}, None)
    print(resultado)