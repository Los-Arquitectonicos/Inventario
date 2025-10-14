"""
Script de Pruebas de Carga con Locust
======================================

Herramienta para probar el requerimiento de escalabilidad
de carga masiva de artículos (100 req/min → 2,000 req/min)

Instalación:
    pip install locust

Ejecución:
    locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000
    
    Luego abrir: http://localhost:8089
    
Configuración recomendada:
    - Para 100 req/min: 2 users, spawn rate 1/s
    - Para 500 req/min: 10 users, spawn rate 2/s  
    - Para 1000 req/min: 20 users, spawn rate 5/s
    - Para 2000 req/min: 40 users, spawn rate 10/s
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, LocalRunner
import random
import time
from datetime import datetime
import json


class GeneradorArticulos:
    """Generador de datos para artículos"""
    
    def __init__(self):
        self.contador = 0
        self.productos_ids = list(range(1, 51))  # IDs de productos existentes
        self.ubicacion_id = 1  # ID de ubicación existente
    
    def generar_codigo_barras(self):
        """Genera código de barras EAN-13 único"""
        self.contador += 1
        base = f"7899{self.contador:08d}"
        
        # Calcular dígito verificador EAN-13
        odd_sum = sum(int(base[i]) for i in range(0, 12, 2))
        even_sum = sum(int(base[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return base + str(check_digit)
    
    def generar_data_articulo(self):
        """Genera datos para crear un artículo"""
        return {
            'producto': random.choice(self.productos_ids),
            'codigo_barras': self.generar_codigo_barras(),
            'ubicacion': self.ubicacion_id
        }


# Instancia global del generador
generador = GeneradorArticulos()

# Estadísticas personalizadas
estadisticas = {
    'exitosos': 0,
    'fallidos': 0,
    'inicio': None,
    'articulos_por_minuto': []
}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al inicio de la prueba"""
    estadisticas['inicio'] = time.time()
    print("\n" + "="*80)
    print("🚀 INICIANDO PRUEBA DE CARGA MASIVA DE ARTÍCULOS")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host: {environment.host}")
    
    if isinstance(environment.runner, (MasterRunner, LocalRunner)):
        print(f"\nObjetivo: Validar escalabilidad de 100 a 2,000 req/min")
        print(f"Requerimiento: 10,000 artículos en < 5 minutos")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al finalizar la prueba"""
    tiempo_total = time.time() - estadisticas['inicio']
    total_requests = estadisticas['exitosos'] + estadisticas['fallidos']
    
    if total_requests > 0:
        tasa_exito = (estadisticas['exitosos'] / total_requests) * 100
        req_por_segundo = total_requests / tiempo_total
        req_por_minuto = req_por_segundo * 60
        
        print("\n" + "="*80)
        print("📊 RESUMEN FINAL DE LA PRUEBA")
        print("="*80)
        print(f"\n⏱️  TIEMPOS:")
        print(f"  Duración total: {tiempo_total:.2f}s ({tiempo_total/60:.2f} min)")
        
        print(f"\n📈 RESULTADOS:")
        print(f"  Total requests: {total_requests:,}")
        print(f"  Exitosos: {estadisticas['exitosos']:,} ({tasa_exito:.2f}%)")
        print(f"  Fallidos: {estadisticas['fallidos']:,}")
        
        print(f"\n⚡ THROUGHPUT:")
        print(f"  Requests/segundo: {req_por_segundo:.2f}")
        print(f"  Requests/minuto: {req_por_minuto:.0f}")
        
        # Evaluación contra objetivos
        print(f"\n🎯 EVALUACIÓN:")
        if req_por_minuto >= 100:
            print(f"  ✅ Supera throughput mínimo (100 req/min)")
        else:
            print(f"  ❌ No alcanza throughput mínimo (100 req/min)")
        
        if req_por_minuto <= 2000:
            print(f"  ✅ Dentro del throughput máximo (2,000 req/min)")
        else:
            print(f"  ⚠️  Excede throughput máximo (2,000 req/min)")
        
        if tasa_exito >= 95:
            print(f"  ✅ Tasa de éxito aceptable (>= 95%)")
        else:
            print(f"  ❌ Tasa de éxito insuficiente (< 95%)")
        
        # Estimación para 10,000 registros
        if req_por_segundo > 0:
            tiempo_estimado_10k = 10000 / req_por_segundo
            print(f"\n⏳ ESTIMACIÓN 10,000 ARTÍCULOS:")
            print(f"  Tiempo estimado: {tiempo_estimado_10k:.2f}s ({tiempo_estimado_10k/60:.2f} min)")
            if tiempo_estimado_10k <= 300:
                print(f"  ✅ Cumple objetivo de < 5 minutos")
            else:
                print(f"  ❌ Excede objetivo de 5 minutos")
        
        # Generar reporte JSON
        reporte = {
            'fecha': datetime.now().isoformat(),
            'duracion_segundos': tiempo_total,
            'total_requests': total_requests,
            'exitosos': estadisticas['exitosos'],
            'fallidos': estadisticas['fallidos'],
            'tasa_exito': tasa_exito,
            'req_por_segundo': req_por_segundo,
            'req_por_minuto': req_por_minuto,
            'tiempo_estimado_10k': 10000 / req_por_segundo if req_por_segundo > 0 else 0,
            'cumple_objetivo_tiempo': (10000 / req_por_segundo) <= 300 if req_por_segundo > 0 else False,
            'cumple_objetivo_tasa': tasa_exito >= 95
        }
        
        with open('reporte_carga_masiva.json', 'w') as f:
            json.dump(reporte, f, indent=2)
        
        print(f"\n📄 Reporte guardado en: reporte_carga_masiva.json")
        print("="*80 + "\n")


class ArticuloUser(HttpUser):
    """
    Usuario simulado que crea artículos mediante POST requests
    """
    
    # Tiempo de espera entre requests (simula comportamiento real)
    wait_time = between(0.1, 0.5)  # 100ms a 500ms
    
    def on_start(self):
        """Se ejecuta al iniciar cada usuario"""
        self.articulos_creados = 0
    
    @task
    def crear_articulo(self):
        """
        Tarea principal: Crear un artículo mediante POST
        """
        data = generador.generar_data_articulo()
        
        with self.client.post(
            "/inventario/articulos/crear/",
            data=data,
            catch_response=True,
            name="POST /inventario/articulos/crear/"
        ) as response:
            
            # Considerar éxito si es redirect (302) o OK (200)
            if response.status_code in [200, 302]:
                estadisticas['exitosos'] += 1
                self.articulos_creados += 1
                response.success()
            else:
                estadisticas['fallidos'] += 1
                response.failure(f"Status code: {response.status_code}")


class ArticuloBatchUser(HttpUser):
    """
    Usuario que usa el endpoint batch para crear artículos en lote
    (si existe endpoint de creación batch)
    """
    
    wait_time = between(1, 3)
    
    @task
    def crear_articulos_batch(self):
        """
        Crear múltiples artículos en un solo request (batch)
        """
        articulos = []
        for _ in range(100):  # Crear 100 artículos por batch
            articulos.append(generador.generar_data_articulo())
        
        data = {'articulos': json.dumps(articulos)}
        
        with self.client.post(
            "/inventario/articulos/crear_batch/",
            json=data,
            catch_response=True,
            name="POST /inventario/articulos/crear_batch/"
        ) as response:
            
            if response.status_code in [200, 201]:
                estadisticas['exitosos'] += len(articulos)
                response.success()
            else:
                estadisticas['fallidos'] += len(articulos)
                response.failure(f"Batch failed: {response.status_code}")


# Para ejecutar con configuraciones predefinidas desde línea de comandos
if __name__ == "__main__":
    import os
    import sys
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    PRUEBA DE CARGA MASIVA - ARTÍCULOS                         ║
║                                                                                ║
║  Requerimiento: Escalar de 100 req/min a 2,000 req/min                       ║
║  Objetivo: Procesar 10,000 registros en < 5 minutos                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Configuraciones disponibles:

1. Baseline (100 req/min)
   locust -f locustfile_articulos.py --host=http://127.0.0.1:8000 \\
          --users 2 --spawn-rate 1 --run-time 1m --headless

2. Media carga (500 req/min)
   locust -f locustfile_articulos.py --host=http://127.0.0.1:8000 \\
          --users 10 --spawn-rate 2 --run-time 2m --headless

3. Alta carga (1,000 req/min)
   locust -f locustfile_articulos.py --host=http://127.0.0.1:8000 \\
          --users 20 --spawn-rate 5 --run-time 3m --headless

4. Máxima carga (2,000 req/min)
   locust -f locustfile_articulos.py --host=http://127.0.0.1:8000 \\
          --users 40 --spawn-rate 10 --run-time 5m --headless

5. Carga objetivo (10,000 artículos)
   locust -f locustfile_articulos.py --host=http://127.0.0.1:8000 \\
          --users 35 --spawn-rate 7 --run-time 5m --headless

6. Interfaz web (configuración manual)
   locust -f locustfile_articulos.py --host=http://127.0.0.1:8000
   Luego abrir: http://localhost:8089

""")
