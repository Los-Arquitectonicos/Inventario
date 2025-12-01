"""
Pruebas de Carga - Sistema de Inventario WMS

Requerimiento:
- Throughput: 100 a 2,000 req/min
- Tiempo: 10,000 registros en menos de 5 minutos
- Tasa de éxito: >= 95%

Uso:
    ./tests/run_load_tests.sh [baseline|medium|high|max|objective]
"""

import random
import time
import json
import os
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, LocalRunner
# Configuración
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from config_entornos import BASE_URL, TIMEOUT, HEADERS
except ImportError:
    BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:8000')
    TIMEOUT = int(os.environ.get('TIMEOUT', '30'))
    HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}

# IDs obtenidos dinámicamente del servidor al inicio de cada prueba
PRODUCTO_IDS = list(range(1, 51))
UBICACION_IDS = [1]  # Lista de ubicaciones disponibles
BODEGA_IDS = [1]     # Lista de bodegas disponibles
IDS_INITIALIZED = False

# Limpieza opcional de artículos antiguos
LIMPIAR_ARTICULOS_VIEJOS = os.environ.get('LIMPIAR_ARTICULOS_VIEJOS', 'false').lower() == 'true'
DIAS_ANTIGUEDAD_LIMPIAR = int(os.environ.get('DIAS_ANTIGUEDAD_LIMPIAR', '1'))

# Generador de Datos
# ═══════════════════════════════════════════════════════════════════════════════

class GeneradorArticulos:
    """Genera códigos de barras EAN-13 únicos usando timestamp + contador."""
    
    def __init__(self):
        self.contador = 0
        self.lock_counter = 0
        
    def generar_codigo_barras_ean13(self):
        """Genera código EAN-13 único con timestamp en microsegundos."""
        self.contador += 1
        
        # Timestamp actual en microsegundos para garantizar unicidad
        timestamp_actual = int(time.time() * 1000000) % 1000000
        unique_num = timestamp_actual * 1000 + (self.contador % 1000)
        
        # Base de 12 dígitos: 789 + 9 dígitos únicos
        base = f"789{unique_num:09d}"
        
        # Calcular dígito verificador EAN-13
        odd_sum = sum(int(base[i]) for i in range(0, 12, 2))
        even_sum = sum(int(base[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return base + str(check_digit)
    
    def generar_articulo(self):
        """Genera datos completos para crear un artículo."""
        return {
            'producto_id': random.choice(PRODUCTO_IDS),
            'codigo_barras': self.generar_codigo_barras_ean13(),
            'ubicacion_id': random.choice(UBICACION_IDS)  # Distribuye entre ubicaciones
        }


generador = GeneradorArticulos()

# Estadísticas
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Optional

class EstadisticasPrueba:
    """Recolector de estadísticas para análisis post-prueba."""
    
    def __init__(self):
        self.inicio: Optional[float] = None
        self.fin: Optional[float] = None
        self.reset()
    
    def reset(self):
        self.inicio = None
        self.fin = None
        self.exitosos = 0
        self.fallidos = 0
        self.errores_por_codigo = {}
        self.tiempos_respuesta = []
        self.articulos_por_segundo = []
        
    def registrar_exito(self, tiempo_respuesta_ms):
        self.exitosos += 1
        self.tiempos_respuesta.append(tiempo_respuesta_ms)
    
    def registrar_fallo(self, codigo_http, mensaje_error=""):
        self.fallidos += 1
        key = f"{codigo_http}: {mensaje_error[:50]}"
        self.errores_por_codigo[key] = self.errores_por_codigo.get(key, 0) + 1
    
    def obtener_estadisticas(self):
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
        
        if duracion > 0:
            stats['req_por_segundo'] = total / duracion
            stats['req_por_minuto'] = (total / duracion) * 60
            stats['articulos_por_segundo'] = self.exitosos / duracion
        else:
            stats['req_por_segundo'] = 0
            stats['req_por_minuto'] = 0
            stats['articulos_por_segundo'] = 0
        
        if stats['articulos_por_segundo'] > 0:
            stats['tiempo_estimado_10k_seg'] = 10000 / stats['articulos_por_segundo']
            stats['tiempo_estimado_10k_min'] = stats['tiempo_estimado_10k_seg'] / 60
            stats['cumple_objetivo_5min'] = stats['tiempo_estimado_10k_seg'] <= 300
        else:
            stats['tiempo_estimado_10k_seg'] = float('inf')
            stats['tiempo_estimado_10k_min'] = float('inf')
            stats['cumple_objetivo_5min'] = False
        
        if self.tiempos_respuesta:
            sorted_times = sorted(self.tiempos_respuesta)
            stats['response_time_min_ms'] = sorted_times[0]
            stats['response_time_max_ms'] = sorted_times[-1]
            stats['response_time_avg_ms'] = sum(sorted_times) / len(sorted_times)
            stats['response_time_p50_ms'] = sorted_times[len(sorted_times) // 2]
            stats['response_time_p95_ms'] = sorted_times[int(len(sorted_times) * 0.95)]
            stats['response_time_p99_ms'] = sorted_times[int(len(sorted_times) * 0.99)]
        
        stats['objetivos'] = {
            'throughput_min_100': stats['req_por_minuto'] >= 100,
            'throughput_max_2000': stats['req_por_minuto'] <= 2000,
            'tiempo_10k_menos_5min': stats['cumple_objetivo_5min'],
            'tasa_exito_95pct': stats['tasa_exito_pct'] >= 95,
        }
        
        stats['errores_detalle'] = self.errores_por_codigo
        
        return stats


stats = EstadisticasPrueba()

# Event Listeners
# ═══════════════════════════════════════════════════════════════════════════════

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicialización: obtiene IDs del servidor y configura estadísticas."""
    global PRODUCTO_IDS, UBICACION_IDS, BODEGA_IDS, IDS_INITIALIZED
    
    stats.reset()
    stats.inicio = time.time()
    
    print("\n" + "=" * 80)
    print("INICIANDO PRUEBA DE CARGA")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host: {environment.host}")
    print(f"Usuarios: {environment.runner.user_count if hasattr(environment.runner, 'user_count') else 'N/A'}")
    print("=" * 80 + "\n")
    
    if not IDS_INITIALIZED:
        try:
            import requests
            print("[INFO] Obteniendo IDs del servidor...")
            
            productos_url = f"{BASE_URL.rstrip('/')}/api/productos/?limit=100"
            resp = requests.get(productos_url, timeout=30)
            if resp.status_code == 200:
                productos_data = resp.json()
                if productos_data.get('productos'):
                    PRODUCTO_IDS = [p['id'] for p in productos_data['productos']]
                    print(f"[OK] {len(PRODUCTO_IDS)} productos disponibles")
            
            ubicaciones_url = f"{BASE_URL.rstrip('/')}/api/ubicaciones/?limit=2000"
            resp = requests.get(ubicaciones_url, timeout=30)
            if resp.status_code == 200:
                ubicaciones_data = resp.json()
                if ubicaciones_data.get('ubicaciones'):
                    UBICACION_IDS = [u['id'] for u in ubicaciones_data['ubicaciones']]
                    print(f"[OK] {len(UBICACION_IDS)} ubicaciones disponibles")
                    
                    # Agrupar por bodegas
                    bodegas_set = set()
                    for u in ubicaciones_data['ubicaciones']:
                        if 'bodega_id' in u:
                            bodegas_set.add(u['bodega_id'])
                        elif 'bodega' in u and isinstance(u['bodega'], dict):
                            bodegas_set.add(u['bodega']['id'])
                    
                    if bodegas_set:
                        BODEGA_IDS = list(bodegas_set)
                        print(f"[OK] {len(BODEGA_IDS)} bodegas disponibles")
            
            if LIMPIAR_ARTICULOS_VIEJOS:
                print(f"\n[INFO] Detectando articulos antiguos (>{DIAS_ANTIGUEDAD_LIMPIAR} dias)...")
                from datetime import timedelta
                fecha_limite = (datetime.now() - timedelta(days=DIAS_ANTIGUEDAD_LIMPIAR)).isoformat()
                
                articulos_url = f"{BASE_URL.rstrip('/')}/api/articulos/?limit=10000"
                resp = requests.get(articulos_url, timeout=60)
                if resp.status_code == 200:
                    articulos = resp.json().get('articulos', [])
                    antiguos = sum(1 for a in articulos if a.get('fecha_ingreso', '') < fecha_limite)
                    if antiguos > 0:
                        print(f"[INFO] {antiguos} articulos antiguos encontrados")
            
            IDS_INITIALIZED = True
            print()
            
        except Exception as e:
            print(f"[ERROR] No se pudieron obtener IDs: {e}")
            print("[INFO] Usando valores por defecto\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalización: calcula y muestra estadísticas."""
    stats.fin = time.time()
    resultados = stats.obtener_estadisticas()
    
    print("\n" + "=" * 80)
    print("RESULTADOS")
    print("=" * 80)
    
    print(f"\nDURACION: {resultados['duracion_segundos']:.2f}s ({resultados['duracion_minutos']:.2f} min)")
    
    print(f"\nREQUESTS:")
    print(f"  Total: {resultados['total_requests']:,}")
    print(f"  Exitosos: {resultados['exitosos']:,} ({resultados['tasa_exito_pct']:.2f}%)")
    print(f"  Fallidos: {resultados['fallidos']:,} ({resultados['tasa_fallo_pct']:.2f}%)")
    
    print(f"\nTHROUGHPUT:")
    print(f"  Requests/segundo: {resultados['req_por_segundo']:.2f}")
    print(f"  Requests/minuto: {resultados['req_por_minuto']:.0f}")
    print(f"  Articulos/segundo: {resultados['articulos_por_segundo']:.2f}")
    
    if 'response_time_avg_ms' in resultados:
        print(f"\nTIEMPOS DE RESPUESTA:")
        print(f"  Promedio: {resultados['response_time_avg_ms']:.2f}ms")
        print(f"  P50: {resultados['response_time_p50_ms']:.2f}ms")
        print(f"  P95: {resultados['response_time_p95_ms']:.2f}ms")
        print(f"  P99: {resultados['response_time_p99_ms']:.2f}ms")
    
    print(f"\nPROYECCION 10,000 ARTICULOS:")
    if resultados['tiempo_estimado_10k_seg'] != float('inf'):
        print(f"  Tiempo estimado: {resultados['tiempo_estimado_10k_seg']:.2f}s ({resultados['tiempo_estimado_10k_min']:.2f} min)")
        print(f"  Objetivo <5 min: {'OK' if resultados['cumple_objetivo_5min'] else 'FALLO'}")
    
    print(f"\nOBJETIVOS:")
    obj = resultados['objetivos']
    print(f"  Throughput >=100 req/min: {'OK' if obj['throughput_min_100'] else 'FALLO'}")
    print(f"  Throughput <=2000 req/min: {'OK' if obj['throughput_max_2000'] else 'ADVERTENCIA'}")
    print(f"  Tiempo 10k <5 min: {'OK' if obj['tiempo_10k_menos_5min'] else 'FALLO'}")
    print(f"  Tasa exito >=95%: {'OK' if obj['tasa_exito_95pct'] else 'FALLO'}")
    
    if resultados['errores_detalle']:
        print(f"\nERRORES:")
        for error, count in list(resultados['errores_detalle'].items())[:5]:
            print(f"  {error}: {count}")
    
    # Guardar reporte JSON en carpeta reportes
    os.makedirs('tests/reportes', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Determinar nombre del perfil desde variable de entorno o runner
    profile_name = os.environ.get('LOCUST_PROFILE', 'unknown')
    filename = f'tests/reportes/reporte_{profile_name}_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte JSON: {filename}")
    print("=" * 80 + "\n")

# Usuarios Simulados
# ═══════════════════════════════════════════════════════════════════════════════

class UsuarioArticulos(HttpUser):
    """Usuario que crea artículos mediante POST."""
    
    wait_time = between(0.1, 0.5)
    host = BASE_URL
    
    def on_start(self):
        self.articulos_creados_usuario = 0
        self.errores_usuario = 0
    
    @task
    def crear_articulo(self):
        """Crea un artículo via POST /articulos/crear/"""
        data = generador.generar_articulo()
        inicio = time.time()
        
        with self.client.post(
            "articulos/crear/",
            json=data,
            timeout=TIMEOUT,
            catch_response=True,
            name="POST /articulos/crear/"
        ) as response:
            tiempo_respuesta_ms = (time.time() - inicio) * 1000
            
            if response.status_code in [200, 201, 302]:
                stats.registrar_exito(tiempo_respuesta_ms)
                self.articulos_creados_usuario += 1
                response.success() # type: ignore
            else:
                error_msg = response.text[:100] if hasattr(response, 'text') else "Unknown error"
                stats.registrar_fallo(response.status_code, error_msg)
                self.errores_usuario += 1
                response.failure(f"HTTP {response.status_code}: {error_msg}") # type: ignore


class UsuarioIntensivo(HttpUser):
    """Usuario que crea artículos sin pausa (carga intensiva)."""
    
    wait_time = between(0, 0.1)
    host = BASE_URL
    
    @task
    def crear_articulo_rapido(self):
        """Crea artículos rapidamente."""
        data = generador.generar_articulo()
        inicio = time.time()
        
        with self.client.post(
            "articulos/crear/",
            json=data,
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



if __name__ == "__main__":
    print(__doc__)

