"""
Pruebas de carga para Lambda Function URL - Servicio de Pedidos
Usa Locust para simular múltiples usuarios creando pedidos concurrentemente
"""

from locust import HttpUser, task, between, events
import random
import json
from datetime import datetime

# URL de la Lambda Function
LAMBDA_FUNCTION_URL = "https://txsntfwdg3cmiliy7d2uo343by0gyzcp.lambda-url.us-east-1.on.aws"

# Datos de prueba para productos
PRODUCTOS_TEST = [
    {"producto_id": 1, "nombre": "Laptop Dell XPS 15", "precio": 1500.00},
    {"producto_id": 2, "nombre": "Monitor LG 27 pulgadas", "precio": 350.00},
    {"producto_id": 3, "nombre": "Teclado mecánico Logitech", "precio": 120.00},
    {"producto_id": 4, "nombre": "Mouse inalámbrico", "precio": 45.00},
    {"producto_id": 5, "nombre": "Webcam HD 1080p", "precio": 80.00},
    {"producto_id": 6, "nombre": "Auriculares Sony WH-1000XM4", "precio": 350.00},
    {"producto_id": 7, "nombre": "SSD Samsung 1TB", "precio": 100.00},
    {"producto_id": 8, "nombre": "RAM DDR4 16GB", "precio": 80.00},
    {"producto_id": 9, "nombre": "Hub USB-C 7 puertos", "precio": 50.00},
    {"producto_id": 10, "nombre": "Cable HDMI 2.1", "precio": 25.00},
]


class PedidosUser(HttpUser):
    """
    Usuario que crea pedidos en el sistema
    Simula comportamiento realista con tiempos de espera entre requests
    """
    
    # Tiempo de espera entre tasks (1-3 segundos)
    wait_time = between(1, 3)
    
    # Configuración del host
    host = LAMBDA_FUNCTION_URL
    
    def on_start(self):
        """Se ejecuta cuando un usuario virtual inicia"""
        self.cliente_id = random.randint(1, 100)
        print(f"🆕 Usuario iniciado - Cliente ID: {self.cliente_id}")
    
    @task(10)
    def crear_pedido_simple(self):
        """
        Crear un pedido con 1-3 productos
        Peso: 10 (más frecuente)
        """
        num_productos = random.randint(1, 3)
        productos = random.sample(PRODUCTOS_TEST, num_productos)
        
        productos_request = [
            {
                "producto_id": p["producto_id"],
                "nombre": p["nombre"],
                "cantidad": random.randint(1, 5),
                "precio": p["precio"]
            }
            for p in productos
        ]
        
        payload = {
            "cliente_id": self.cliente_id,
            "productos": productos_request,
            "notas": f"Pedido de prueba carga - {datetime.now().isoformat()}"
        }
        
        with self.client.post(
            "/pedidos",
            json=payload,
            catch_response=True,
            name="POST /pedidos (1-3 productos)"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def crear_pedido_grande(self):
        """
        Crear un pedido con 5-8 productos
        Peso: 5 (menos frecuente)
        """
        num_productos = random.randint(5, 8)
        productos = random.sample(PRODUCTOS_TEST, num_productos)
        
        productos_request = [
            {
                "producto_id": p["producto_id"],
                "nombre": p["nombre"],
                "cantidad": random.randint(1, 10),
                "precio": p["precio"]
            }
            for p in productos
        ]
        
        payload = {
            "cliente_id": self.cliente_id,
            "productos": productos_request,
            "notas": f"Pedido grande - {datetime.now().isoformat()}"
        }
        
        with self.client.post(
            "/pedidos",
            json=payload,
            catch_response=True,
            name="POST /pedidos (5-8 productos)"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def listar_pedidos(self):
        """
        Listar todos los pedidos
        Peso: 3
        """
        with self.client.get(
            "/pedidos",
            catch_response=True,
            name="GET /pedidos"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def listar_pedidos_cliente(self):
        """
        Listar pedidos de un cliente específico
        Peso: 2
        """
        with self.client.get(
            f"/pedidos?cliente_id={self.cliente_id}",
            catch_response=True,
            name="GET /pedidos?cliente_id=X"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# Event listeners para métricas personalizadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta cuando inicia la prueba"""
    print("\n" + "="*80)
    print("🚀 INICIANDO PRUEBAS DE CARGA - SERVICIO DE PEDIDOS")
    print("="*80)
    print(f"📍 Lambda URL: {LAMBDA_FUNCTION_URL}")
    print(f"🎯 Endpoint: POST /pedidos")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta cuando termina la prueba"""
    print("\n" + "="*80)
    print("✅ PRUEBAS DE CARGA COMPLETADAS")
    print("="*80)
    print("📊 Revisa el reporte en la interfaz web de Locust")
    print("="*80 + "\n")


# Configuración para ejecución headless (sin UI)
if __name__ == "__main__":
    import os
    import subprocess
    
    print("\n🔧 Configuración de Locust")
    print("="*80)
    print("Para ejecutar las pruebas, usa uno de estos comandos:\n")
    print("1️⃣  CON INTERFAZ WEB (recomendado):")
    print("   locust -f locustfile.py --host=" + LAMBDA_FUNCTION_URL)
    print("   Luego abre: http://localhost:8089\n")
    print("2️⃣  SIN INTERFAZ (headless):")
    print("   locust -f locustfile.py --host=" + LAMBDA_FUNCTION_URL + " \\")
    print("          --users 10 --spawn-rate 2 --run-time 2m --headless\n")
    print("="*80 + "\n")
