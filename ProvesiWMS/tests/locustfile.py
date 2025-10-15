"""
═══════════════════════════════════════════════════════════════════════════════
LOCUST LOAD TESTING - INVENTARIO WMS
═══════════════════════════════════════════════════════════════════════════════

Requerimiento Arquitectónico:
"Cuando realizo operaciones de carga masiva de inventario, quiero que el 
sistema incremente su capacidad de procesamiento desde 100 peticiones por 
minuto hasta 2.000 peticiones por minuto, asegurando que cada carga de 
10.000 registros se complete en menos de 5 minutos conforme crece la demanda."

Validaciones:
- Throughput: 100 → 2,000 req/min
- Tiempo: 10,000 registros en < 5 minutos
- Integridad: Validación de datos
- Consistencia: Sin inconsistencias en DB
- Escalabilidad: Sin degradación bajo carga
- Resiliencia: Manejo de errores parciales

Instalación:
    pip install locust

Uso:
    # Interfaz web (recomendado para exploración)
    locust -f tests/locustfile.py
    
    # Línea de comandos (automatizado)
    ./tests/run_load_tests.sh

Configuración:
    Editar tests/config_entornos.py para cambiar:
    - BASE_URL (local, AWS ALB, producción)
    - TIMEOUT
    - HEADERS (autenticación)

Arquitectura:
    - PostgreSQL en producción (actualmente SQLite para desarrollo)
    - Puerto configurable para load balancer
    - Simulación realista de usuarios concurrentes
    - Métricas detalladas y reportes JSON

═══════════════════════════════════════════════════════════════════════════════
"""

import random
import time
import json
import os
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, LocalRunner
# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from config_entornos import BASE_URL, TIMEOUT, HEADERS
except ImportError:
    # Valores por defecto si no existe config_entornos.py
    BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:8000')
    TIMEOUT = int(os.environ.get('TIMEOUT', '30'))
    HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}

# IDs de recursos existentes (deben existir en DB antes de correr tests)
# Ajustar según tu base de datos
PRODUCTO_IDS = list(range(1, 51))  # Productos 1-50
UBICACION_ID = int(os.environ.get('UBICACION_ID', '1'))
BODEGA_ID = int(os.environ.get('BODEGA_ID', '1'))


# ═══════════════════════════════════════════════════════════════════════════════
# GENERADOR DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

class GeneradorArticulos:
    """
    Generador thread-safe de datos para artículos con códigos EAN-13 únicos.
    """
    
    def __init__(self):
        self.contador = 0
        self.lock_counter = 0  # Para sincronización básica
        
    def generar_codigo_barras_ean13(self):
        """
        Genera código de barras EAN-13 único con dígito verificador correcto.
        
        Formato: 789XXXXXXXXC donde C es el dígito verificador
        """
        self.contador += 1
        # Base de 12 dígitos: 789 + 9 dígitos del contador
        base = f"789{self.contador:09d}"
        
        # Calcular dígito verificador EAN-13
        odd_sum = sum(int(base[i]) for i in range(0, 12, 2))
        even_sum = sum(int(base[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return base + str(check_digit)
    
    def generar_articulo(self):
        """
        Genera datos completos para crear un artículo.
        
        Returns:
            dict: Datos del artículo listos para POST request
        """
        return {
            'producto': random.choice(PRODUCTO_IDS),
            'codigo_barras': self.generar_codigo_barras_ean13(),
            'ubicacion': UBICACION_ID
        }


# Instancia global del generador
generador = GeneradorArticulos()


# ═══════════════════════════════════════════════════════════════════════════════
# ESTADÍSTICAS Y MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Optional

class EstadisticasPrueba:
    """
    Recolector de estadísticas para análisis post-prueba.
    """
    
    def __init__(self):
        self.inicio: Optional[float] = None
        self.fin: Optional[float] = None
        self.reset()
    
    def reset(self):
        """Reinicia todas las estadísticas."""
        self.inicio = None
        self.fin = None
        self.exitosos = 0
        self.fallidos = 0
        self.errores_por_codigo = {}
        self.tiempos_respuesta = []
        self.articulos_por_segundo = []
        
    def registrar_exito(self, tiempo_respuesta_ms):
        """Registra un request exitoso."""
        self.exitosos += 1
        self.tiempos_respuesta.append(tiempo_respuesta_ms)
    
    def registrar_fallo(self, codigo_http, mensaje_error=""):
        """Registra un request fallido."""
        self.fallidos += 1
        key = f"{codigo_http}: {mensaje_error[:50]}"
        self.errores_por_codigo[key] = self.errores_por_codigo.get(key, 0) + 1
    
    def obtener_estadisticas(self):
        """
        Calcula y retorna estadísticas completas.
        
        Returns:
            dict: Estadísticas detalladas de la prueba
        """
        total = self.exitosos + self.fallidos
        duracion = (self.fin - self.inicio) if self.fin and self.inicio else 0
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'duracion_segundos': duracion,
            'duracion_minutos': duracion / 60,
            'total_requests': total,
            'exitosos': self.exitosos,
            'fallidos': self.fallidos,
            'tasa_exito_pct': (self.exitosos / total * 100) if total > 0 else 0,
            'tasa_fallo_pct': (self.fallidos / total * 100) if total > 0 else 0,
        }
        
        # Throughput
        if duracion > 0:
            stats['req_por_segundo'] = total / duracion
            stats['req_por_minuto'] = (total / duracion) * 60
            stats['articulos_por_segundo'] = self.exitosos / duracion
        else:
            stats['req_por_segundo'] = 0
            stats['req_por_minuto'] = 0
            stats['articulos_por_segundo'] = 0
        
        # Proyección a 10,000 artículos
        if stats['articulos_por_segundo'] > 0:
            stats['tiempo_estimado_10k_seg'] = 10000 / stats['articulos_por_segundo']
            stats['tiempo_estimado_10k_min'] = stats['tiempo_estimado_10k_seg'] / 60
            stats['cumple_objetivo_5min'] = stats['tiempo_estimado_10k_seg'] <= 300
        else:
            stats['tiempo_estimado_10k_seg'] = float('inf')
            stats['tiempo_estimado_10k_min'] = float('inf')
            stats['cumple_objetivo_5min'] = False
        
        # Tiempos de respuesta
        if self.tiempos_respuesta:
            sorted_times = sorted(self.tiempos_respuesta)
            stats['response_time_min_ms'] = sorted_times[0]
            stats['response_time_max_ms'] = sorted_times[-1]
            stats['response_time_avg_ms'] = sum(sorted_times) / len(sorted_times)
            stats['response_time_p50_ms'] = sorted_times[len(sorted_times) // 2]
            stats['response_time_p95_ms'] = sorted_times[int(len(sorted_times) * 0.95)]
            stats['response_time_p99_ms'] = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Evaluación de objetivos
        stats['objetivos'] = {
            'throughput_min_100': stats['req_por_minuto'] >= 100,
            'throughput_max_2000': stats['req_por_minuto'] <= 2000,
            'tiempo_10k_menos_5min': stats['cumple_objetivo_5min'],
            'tasa_exito_95pct': stats['tasa_exito_pct'] >= 95,
        }
        
        # Errores
        stats['errores_detalle'] = self.errores_por_codigo
        
        return stats


# Instancia global de estadísticas
stats = EstadisticasPrueba()


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT LISTENERS
# ═══════════════════════════════════════════════════════════════════════════════

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al iniciar la prueba."""
    stats.reset()
    stats.inicio = time.time()
    
    print("\n" + "=" * 80)
    print("INICIANDO PRUEBA DE CARGA MASIVA")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host: {environment.host}")
    print(f"Timeout: {TIMEOUT}s")
    print(f"Usuarios: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print()
    print("OBJETIVOS:")
    print("  - Throughput: 100-2,000 req/min")
    print("  - Procesar: 10,000 artículos en < 5 minutos")
    print("  - Tasa de éxito: >= 95%")
    print("  - Sin degradación bajo carga")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al finalizar la prueba."""
    stats.fin = time.time()
    resultados = stats.obtener_estadisticas()
    
    # Imprimir resumen en consola
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    print(f"\nDURACION:")
    print(f"  Total: {resultados['duracion_segundos']:.2f}s ({resultados['duracion_minutos']:.2f} min)")
    
    print(f"\nREQUESTS:")
    print(f"  Total: {resultados['total_requests']:,}")
    print(f"  Exitosos: {resultados['exitosos']:,} ({resultados['tasa_exito_pct']:.2f}%)")
    print(f"  Fallidos: {resultados['fallidos']:,} ({resultados['tasa_fallo_pct']:.2f}%)")
    
    print(f"\nTHROUGHPUT:")
    print(f"  Requests/segundo: {resultados['req_por_segundo']:.2f}")
    print(f"  Requests/minuto: {resultados['req_por_minuto']:.0f}")
    print(f"  Artículos/segundo: {resultados['articulos_por_segundo']:.2f}")
    
    if 'response_time_avg_ms' in resultados:
        print(f"\nTIEMPOS DE RESPUESTA:")
        print(f"  Promedio: {resultados['response_time_avg_ms']:.2f}ms")
        print(f"  P50 (Mediana): {resultados['response_time_p50_ms']:.2f}ms")
        print(f"  P95: {resultados['response_time_p95_ms']:.2f}ms")
        print(f"  P99: {resultados['response_time_p99_ms']:.2f}ms")
        print(f"  Min: {resultados['response_time_min_ms']:.2f}ms")
        print(f"  Max: {resultados['response_time_max_ms']:.2f}ms")
    
    print(f"\nPROYECCION 10,000 ARTICULOS:")
    if resultados['tiempo_estimado_10k_seg'] != float('inf'):
        print(f"  Tiempo estimado: {resultados['tiempo_estimado_10k_seg']:.2f}s ({resultados['tiempo_estimado_10k_min']:.2f} min)")
        if resultados['cumple_objetivo_5min']:
            print(f"  [OK] CUMPLE objetivo de < 5 minutos")
        else:
            print(f"  [FALLO] NO CUMPLE objetivo de < 5 minutos")
    else:
        print(f"  [ADVERTENCIA] No se pudieron crear artículos (sin datos)")
    
    print(f"\nEVALUACION DE OBJETIVOS:")
    obj = resultados['objetivos']
    print(f"  [{'OK' if obj['throughput_min_100'] else 'FALLO'}] Throughput mínimo (>=100 req/min)")
    print(f"  [{'OK' if obj['throughput_max_2000'] else 'ADVERTENCIA'}] Throughput dentro de rango (<=2,000 req/min)")
    print(f"  [{'OK' if obj['tiempo_10k_menos_5min'] else 'FALLO'}] Tiempo 10k artículos (< 5 min)")
    print(f"  [{'OK' if obj['tasa_exito_95pct'] else 'FALLO'}] Tasa de éxito (>=95%)")
    
    # Mostrar errores si existen
    if resultados['errores_detalle']:
        print(f"\nERRORES DETECTADOS:")
        for error, count in list(resultados['errores_detalle'].items())[:10]:
            print(f"  - {error}: {count} veces")
        if len(resultados['errores_detalle']) > 10:
            print(f"  ... y {len(resultados['errores_detalle']) - 10} tipos de errores más")
    
    # Guardar reporte JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'tests/reporte_locust_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte guardado: {filename}")
    print("=" * 80 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# USUARIOS SIMULADOS
# ═══════════════════════════════════════════════════════════════════════════════

class UsuarioArticulos(HttpUser):
    """
    Usuario simulado que crea artículos individualmente.
    
    Simula comportamiento realista con tiempos de espera entre requests.
    """
    
    # Tiempo de espera entre requests (think time)
    wait_time = between(0.1, 0.5)  # 100-500ms
    
    # Host se configura desde línea de comandos o usa BASE_URL
    host = BASE_URL
    
    def on_start(self):
        """Se ejecuta al iniciar cada usuario."""
        self.articulos_creados_usuario = 0
        self.errores_usuario = 0
    
    @task(10)  # Peso 10: tarea más frecuente
    def crear_articulo(self):
        """
        Crea un artículo mediante POST al endpoint de creación.
        """
        data = generador.generar_articulo()
        
        inicio = time.time()
        
        with self.client.post(
            "/inventario/articulos/crear/",
            data=data,
            timeout=TIMEOUT,
            catch_response=True,
            name="POST /articulos/crear/"
        ) as response:
            
            tiempo_respuesta_ms = (time.time() - inicio) * 1000
            
            # Django redirige con 302 después de crear
            if response.status_code in [200, 201, 302]:
                stats.registrar_exito(tiempo_respuesta_ms)
                self.articulos_creados_usuario += 1
                response.success() # type: ignore
            else:
                error_msg = response.text[:100] if hasattr(response, 'text') else "Unknown error"
                stats.registrar_fallo(response.status_code, error_msg)
                self.errores_usuario += 1
                response.failure(f"HTTP {response.status_code}: {error_msg}") # type: ignore
    
    @task(1)  # Peso 1: tarea ocasional
    def listar_articulos(self):
        """
        Lista artículos mediante GET (para simular lectura realista).
        """
        with self.client.get(
            "/inventario/articulos/",
            timeout=TIMEOUT,
            catch_response=True,
            name="GET /articulos/"
        ) as response:
            
            if response.status_code == 200:
                response.success() # type: ignore
            else:
                response.failure(f"HTTP {response.status_code}") # type: ignore
    
    @task(1)  # Peso 1: tarea ocasional
    def ver_productos(self):
        """
        Consulta productos (operación de lectura común).
        """
        with self.client.get(
            "/inventario/productos/",
            timeout=TIMEOUT,
            catch_response=True,
            name="GET /productos/"
        ) as response:
            
            if response.status_code == 200:
                response.success() # type: ignore
            else:
                response.failure(f"HTTP {response.status_code}") # type: ignore


class UsuarioIntensivo(HttpUser):
    """
    Usuario que solo crea artículos sin pausa (carga intensiva).
    
    Útil para pruebas de estrés y saturación del sistema.
    """
    
    wait_time = between(0, 0.1)  # Casi sin espera
    host = BASE_URL
    
    @task
    def crear_articulo_rapido(self):
        """Crea artículos rápidamente sin pausas."""
        data = generador.generar_articulo()
        
        inicio = time.time()
        
        with self.client.post(
            "/inventario/articulos/crear/",
            data=data,
            timeout=TIMEOUT,
            catch_response=True,
            name="POST /articulos/crear/ (intensivo)"
        ) as response:
            
            tiempo_respuesta_ms = (time.time() - inicio) * 1000
            
            if response.status_code in [200, 201, 302]:
                stats.registrar_exito(tiempo_respuesta_ms)
                response.success() # type: ignore
            else:
                error_msg = response.text[:100] if hasattr(response, 'text') else "Unknown error"
                stats.registrar_fallo(response.status_code, error_msg)
                response.failure(f"HTTP {response.status_code}") # type: ignore


# ═══════════════════════════════════════════════════════════════════════════════
# INFORMACIÓN DE USO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    LOCUST - PRUEBAS DE CARGA MASIVA                           ║
║                           Inventario WMS                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📋 CONFIGURACIONES RECOMENDADAS:

1️⃣  Baseline (100 req/min) - 1 minuto:
   locust -f tests/locustfile.py --users 2 --spawn-rate 1 --run-time 1m --headless

2️⃣  Media carga (500 req/min) - 2 minutos:
   locust -f tests/locustfile.py --users 10 --spawn-rate 2 --run-time 2m --headless

3️⃣  Alta carga (1,000 req/min) - 3 minutos:
   locust -f tests/locustfile.py --users 20 --spawn-rate 5 --run-time 3m --headless

4️⃣  Máxima carga (2,000 req/min) - 5 minutos:
   locust -f tests/locustfile.py --users 40 --spawn-rate 10 --run-time 5m --headless

5️⃣  Prueba objetivo (10,000 artículos) - 5 minutos:
   locust -f tests/locustfile.py --users 35 --spawn-rate 7 --run-time 5m --headless

6️⃣  Interfaz web (exploración manual):
   locust -f tests/locustfile.py
   → Abrir: http://localhost:8089

🚀 USO RÁPIDO:
   Ejecutar script todo-en-uno:
   ./tests/run_load_tests.sh

📝 CONFIGURACIÓN:
   Editar: tests/config_entornos.py
   - BASE_URL (local/AWS/producción)
   - TIMEOUT
   - HEADERS

📊 REPORTES:
   Generados automáticamente en: tests/reporte_locust_YYYYMMDD_HHMMSS.json

═══════════════════════════════════════════════════════════════════════════════
    """)
