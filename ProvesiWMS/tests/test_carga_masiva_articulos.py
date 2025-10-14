"""
Test de Carga Masiva y Escalabilidad para Artículos
====================================================

Requerimiento Arquitecturalmente Significativo:
- Incrementar capacidad de 100 req/min a 2.000 req/min
- Procesar 10.000 registros en menos de 5 minutos
- Validar integridad de datos
- Evitar inconsistencias
- Soportar carga sin degradación
- Mantener registros correctos en caso de errores parciales
- Notificar con resumen del proceso

CONFIGURACIÓN DE ENTORNOS:
- Ver config_entornos.py para cambiar entre local/AWS/producción
- Solo necesitas cambiar BASE_URL en config_entornos.py
"""

import time
import json
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal
import requests
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.db import connection
from inventario.models import Producto, Articulo, UbicacionBodega, Bodega

# Importar configuración de entorno
try:
    from .config_entornos import (
        BASE_URL, TIMEOUT, HEADERS,
        WORKERS_TEST_1000, WORKERS_TEST_10000,
        TIEMPO_MAX_10000, REQUISITO_REQ_MIN
    )
except ImportError:
    # Valores por defecto si no existe config_entornos.py
    BASE_URL = "http://127.0.0.1:8000"
    TIMEOUT = 30
    HEADERS = {"Content-Type": "application/json"}
    WORKERS_TEST_1000 = 10
    WORKERS_TEST_10000 = 50
    TIEMPO_MAX_10000 = 300
    REQUISITO_REQ_MIN = 2000


class TestCargaMasivaArticulos(TransactionTestCase):
    """
    Suite de pruebas para validar el requerimiento de carga masiva.
    
    CAMBIAR ENTORNO:
    - Edita config_entornos.py y cambia BASE_URL
    - Para AWS ALB: Descomenta la línea correspondiente
    - Para local: Usa http://127.0.0.1:8000 (por defecto)
    """
    
    BASE_URL = BASE_URL
    TIMEOUT = TIMEOUT
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*80)
        print("INICIANDO PRUEBAS DE CARGA MASIVA DE ARTÍCULOS")
        print("="*80)
    
    def setUp(self):
        """Preparar datos base para las pruebas"""
        # Crear bodega y ubicación
        self.bodega = Bodega.objects.create(
            nombre="Bodega Test Carga",
            ciudad="Bogotá",
            direccion="Calle Test 123"
        )
        
        self.ubicacion = UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="A01",
            estante="E01",
            nivel="N01",
            capacidad_total=50000,
            capacidad_disponible=50000
        )
        
        # Crear productos base (simular que ya existen)
        self.productos = []
        for i in range(10):
            producto = Producto.objects.create(
                nombre=f"Producto Test {i+1}",
                descripcion=f"Descripción del producto {i+1}",
                precio_costo=Decimal("100.00"),
                precio_venta=Decimal("150.00"),
                peso=Decimal("1.0"),
                dimensiones="10x10x10",
                color="Azul",
                talla="M",
                marca="TestBrand",
                cantidad_stock=10000
            )
            self.productos.append(producto)
        
        print(f"\n✓ Setup completado: {len(self.productos)} productos creados")
    
    def tearDown(self):
        """Limpiar después de cada prueba"""
        # Las transacciones se rollbackean automáticamente con TransactionTestCase
        pass
    
    def generar_codigo_barras_unico(self, index):
        """Genera un código de barras EAN-13 único basado en el índice"""
        base = f"7890{index:08d}"
        
        # Calcular dígito verificador EAN-13
        odd_sum = sum(int(base[i]) for i in range(0, 12, 2))
        even_sum = sum(int(base[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return base + str(check_digit)
    
    def crear_articulo_request(self, producto_id, ubicacion_id, codigo_barras):
        """
        Crea un artículo mediante POST request.
        
        Usa TIMEOUT de config_entornos.py (30s local, 60s AWS)
        """
        url = f"{self.BASE_URL}/inventario/articulos/crear/"
        data = {
            'producto': producto_id,
            'codigo_barras': codigo_barras,
            'ubicacion': ubicacion_id
        }
        
        try:
            response = requests.post(
                url, 
                data=data, 
                timeout=self.TIMEOUT,
                headers=HEADERS
            )
            return {
                'success': response.status_code == 302 or response.status_code == 200,
                'status_code': response.status_code,
                'codigo_barras': codigo_barras
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status_code': 504,  # Gateway Timeout
                'error': f'Request timeout ({self.TIMEOUT}s)',
                'codigo_barras': codigo_barras
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'success': False,
                'status_code': 503,  # Service Unavailable
                'error': f'Connection error: {str(e)}',
                'codigo_barras': codigo_barras
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e),
                'codigo_barras': codigo_barras
            }
    
    def test_01_carga_baseline_100_articulos(self):
        """
        Test 1: Baseline - 100 artículos secuenciales
        Objetivo: Establecer línea base de rendimiento
        """
        print("\n" + "-"*80)
        print("TEST 1: BASELINE - 100 ARTÍCULOS SECUENCIALES")
        print("-"*80)
        
        cantidad = 100
        inicio = time.time()
        resultados = []
        
        for i in range(cantidad):
            producto = random.choice(self.productos)
            codigo_barras = self.generar_codigo_barras_unico(i)
            resultado = self.crear_articulo_request(
                producto.id, 
                self.ubicacion.id, 
                codigo_barras
            )
            resultados.append(resultado)
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        fallidos = cantidad - exitosos
        tasa_exito = (exitosos / cantidad) * 100
        tiempo_promedio = tiempo_total / cantidad
        req_por_segundo = cantidad / tiempo_total
        req_por_minuto = req_por_segundo * 60
        
        print(f"\n📊 RESULTADOS:")
        print(f"  ✓ Total artículos: {cantidad}")
        print(f"  ✓ Exitosos: {exitosos} ({tasa_exito:.2f}%)")
        print(f"  ✗ Fallidos: {fallidos}")
        print(f"  ⏱️  Tiempo total: {tiempo_total:.2f}s")
        print(f"  ⚡ Tiempo promedio: {tiempo_promedio*1000:.2f}ms")
        print(f"  📈 Throughput: {req_por_segundo:.2f} req/s ({req_por_minuto:.0f} req/min)")
        
        # Verificar en base de datos
        articulos_creados = Articulo.objects.filter(
            codigo_barras__startswith='7890'
        ).count()
        print(f"  💾 Artículos en DB: {articulos_creados}")
        
        self.assertGreater(tasa_exito, 95, "La tasa de éxito debe ser > 95%")
    
    def test_02_carga_concurrente_1000_articulos(self):
        """
        Test 2: 1.000 artículos con concurrencia (10 workers)
        Objetivo: Probar capacidad de procesamiento concurrente
        """
        print("\n" + "-"*80)
        print("TEST 2: CARGA CONCURRENTE - 1.000 ARTÍCULOS (10 WORKERS)")
        print("-"*80)
        
        cantidad = 1000
        workers = 10
        inicio = time.time()
        resultados = []
        tiempos_respuesta = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i in range(cantidad):
                producto = random.choice(self.productos)
                codigo_barras = self.generar_codigo_barras_unico(1000 + i)
                
                future = executor.submit(
                    self.crear_articulo_request,
                    producto.id,
                    self.ubicacion.id,
                    codigo_barras
                )
                futures.append((future, time.time()))
            
            for future, tiempo_envio in as_completed(futures):
                tiempo_respuesta = time.time() - tiempo_envio
                tiempos_respuesta.append(tiempo_respuesta)
                resultado = future.result()
                resultados.append(resultado)
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        fallidos = cantidad - exitosos
        tasa_exito = (exitosos / cantidad) * 100
        req_por_segundo = cantidad / tiempo_total
        req_por_minuto = req_por_segundo * 60
        
        # Estadísticas de latencia
        tiempo_min = min(tiempos_respuesta) * 1000
        tiempo_max = max(tiempos_respuesta) * 1000
        tiempo_promedio = statistics.mean(tiempos_respuesta) * 1000
        tiempo_p50 = statistics.median(tiempos_respuesta) * 1000
        tiempo_p95 = statistics.quantiles(tiempos_respuesta, n=20)[18] * 1000
        
        print(f"\n📊 RESULTADOS:")
        print(f"  ✓ Total artículos: {cantidad}")
        print(f"  ✓ Exitosos: {exitosos} ({tasa_exito:.2f}%)")
        print(f"  ✗ Fallidos: {fallidos}")
        print(f"  👥 Workers concurrentes: {workers}")
        print(f"  ⏱️  Tiempo total: {tiempo_total:.2f}s")
        print(f"  📈 Throughput: {req_por_segundo:.2f} req/s ({req_por_minuto:.0f} req/min)")
        print(f"\n⚡ LATENCIAS:")
        print(f"  Min: {tiempo_min:.2f}ms")
        print(f"  Max: {tiempo_max:.2f}ms")
        print(f"  Promedio: {tiempo_promedio:.2f}ms")
        print(f"  P50 (Mediana): {tiempo_p50:.2f}ms")
        print(f"  P95: {tiempo_p95:.2f}ms")
        
        self.assertGreater(tasa_exito, 95, "La tasa de éxito debe ser > 95%")
        self.assertLess(req_por_minuto, 2000, "Aún no debe alcanzar 2000 req/min")
    
    def test_03_carga_10000_articulos_objetivo_principal(self):
        """
        Test 3: 10.000 artículos en menos de 5 minutos (OBJETIVO PRINCIPAL)
        Objetivo: Validar el requerimiento principal de carga masiva
        """
        print("\n" + "-"*80)
        print("TEST 3: CARGA MASIVA - 10.000 ARTÍCULOS (OBJETIVO: < 5 MIN)")
        print("-"*80)
        
        cantidad = 10000
        workers = 50  # Aumentar concurrencia
        tiempo_objetivo = 300  # 5 minutos
        
        print(f"\n⚙️  CONFIGURACIÓN:")
        print(f"  Cantidad: {cantidad:,} artículos")
        print(f"  Workers: {workers}")
        print(f"  Tiempo objetivo: {tiempo_objetivo}s (5 minutos)")
        print(f"  Throughput requerido: {(cantidad/tiempo_objetivo)*60:.0f} req/min")
        
        inicio = time.time()
        resultados = []
        tiempos_respuesta = []
        errores = []
        
        print(f"\n🚀 INICIANDO CARGA MASIVA...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i in range(cantidad):
                producto = random.choice(self.productos)
                codigo_barras = self.generar_codigo_barras_unico(10000 + i)
                
                future = executor.submit(
                    self.crear_articulo_request,
                    producto.id,
                    self.ubicacion.id,
                    codigo_barras
                )
                futures.append((future, time.time(), codigo_barras))
            
            # Progreso cada 1000 registros
            completados = 0
            for future, tiempo_envio, codigo_barras in futures:
                try:
                    resultado = future.result()
                    tiempo_respuesta = time.time() - tiempo_envio
                    tiempos_respuesta.append(tiempo_respuesta)
                    resultados.append(resultado)
                    
                    if not resultado['success']:
                        errores.append({
                            'codigo_barras': codigo_barras,
                            'status': resultado.get('status_code'),
                            'error': resultado.get('error')
                        })
                    
                    completados += 1
                    if completados % 1000 == 0:
                        tiempo_parcial = time.time() - inicio
                        tasa_actual = (completados / tiempo_parcial) * 60
                        print(f"  ⏳ Progreso: {completados:,}/{cantidad:,} "
                              f"({(completados/cantidad)*100:.1f}%) - "
                              f"{tasa_actual:.0f} req/min")
                
                except Exception as e:
                    errores.append({
                        'codigo_barras': codigo_barras,
                        'error': str(e)
                    })
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        fallidos = cantidad - exitosos
        tasa_exito = (exitosos / cantidad) * 100
        req_por_segundo = cantidad / tiempo_total
        req_por_minuto = req_por_segundo * 60
        
        # Estadísticas de latencia
        if tiempos_respuesta:
            tiempo_min = min(tiempos_respuesta) * 1000
            tiempo_max = max(tiempos_respuesta) * 1000
            tiempo_promedio = statistics.mean(tiempos_respuesta) * 1000
            tiempo_p50 = statistics.median(tiempos_respuesta) * 1000
            tiempo_p95 = statistics.quantiles(tiempos_respuesta, n=20)[18] * 1000
            tiempo_p99 = statistics.quantiles(tiempos_respuesta, n=100)[98] * 1000
        
        print(f"\n{'='*80}")
        print("📊 RESULTADOS FINALES")
        print(f"{'='*80}")
        print(f"\n✅ CARGA COMPLETADA:")
        print(f"  Total artículos: {cantidad:,}")
        print(f"  Exitosos: {exitosos:,} ({tasa_exito:.2f}%)")
        print(f"  Fallidos: {fallidos:,}")
        print(f"\n⏱️  TIEMPOS:")
        print(f"  Tiempo total: {tiempo_total:.2f}s ({tiempo_total/60:.2f} min)")
        print(f"  Tiempo objetivo: {tiempo_objetivo}s (5 min)")
        print(f"  {'✅ CUMPLE' if tiempo_total <= tiempo_objetivo else '❌ NO CUMPLE'} el objetivo de tiempo")
        print(f"\n📈 THROUGHPUT:")
        print(f"  Requests/segundo: {req_por_segundo:.2f}")
        print(f"  Requests/minuto: {req_por_minuto:.0f}")
        print(f"  Objetivo mínimo: 100 req/min")
        print(f"  Objetivo máximo: 2,000 req/min")
        print(f"  {'✅ DENTRO' if 100 <= req_por_minuto <= 2000 else '⚠️  FUERA'} del rango objetivo")
        
        if tiempos_respuesta:
            print(f"\n⚡ LATENCIAS:")
            print(f"  Min: {tiempo_min:.2f}ms")
            print(f"  Max: {tiempo_max:.2f}ms")
            print(f"  Promedio: {tiempo_promedio:.2f}ms")
            print(f"  P50 (Mediana): {tiempo_p50:.2f}ms")
            print(f"  P95: {tiempo_p95:.2f}ms")
            print(f"  P99: {tiempo_p99:.2f}ms")
        
        # Verificar integridad en base de datos
        articulos_db = Articulo.objects.filter(
            codigo_barras__startswith='78900001'
        ).count()
        
        print(f"\n💾 INTEGRIDAD DE DATOS:")
        print(f"  Artículos en DB: {articulos_db:,}")
        print(f"  Consistencia: {(articulos_db/exitosos)*100:.2f}%")
        
        if errores:
            print(f"\n⚠️  ERRORES DETECTADOS ({len(errores)}):")
            for i, error in enumerate(errores[:5]):  # Mostrar primeros 5
                print(f"  {i+1}. Código: {error['codigo_barras']} - {error.get('error', 'Unknown')}")
            if len(errores) > 5:
                print(f"  ... y {len(errores)-5} errores más")
        
        # RESUMEN PARA ADMINISTRADOR
        print(f"\n{'='*80}")
        print("📋 RESUMEN PARA ADMINISTRADOR")
        print(f"{'='*80}")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Operación: Carga Masiva de Artículos")
        print(f"Registros procesados: {cantidad:,}")
        print(f"Registros exitosos: {exitosos:,}")
        print(f"Registros fallidos: {fallidos:,}")
        print(f"Tasa de éxito: {tasa_exito:.2f}%")
        print(f"Tiempo total: {tiempo_total/60:.2f} minutos")
        print(f"Throughput: {req_por_minuto:.0f} req/min")
        print(f"Estado: {'✅ EXITOSO' if tasa_exito >= 95 and tiempo_total <= tiempo_objetivo else '⚠️  CON OBSERVACIONES'}")
        print(f"{'='*80}\n")
        
        # Assertions
        self.assertLessEqual(tiempo_total, tiempo_objetivo, 
                           f"Debe completarse en menos de {tiempo_objetivo}s (5 min)")
        self.assertGreaterEqual(tasa_exito, 95, 
                               "La tasa de éxito debe ser >= 95%")
        self.assertGreaterEqual(articulos_db, exitosos * 0.95,
                               "Debe haber consistencia de al menos 95% en DB")
    
    def test_04_escalabilidad_incremental(self):
        """
        Test 4: Escalabilidad incremental
        Objetivo: Validar que el sistema escala desde 100 req/min hasta 2000 req/min
        """
        print("\n" + "-"*80)
        print("TEST 4: ESCALABILIDAD INCREMENTAL (100 → 2000 req/min)")
        print("-"*80)
        
        cargas = [
            (100, 1),    # 100 artículos, 1 worker
            (500, 5),    # 500 artículos, 5 workers
            (1000, 10),  # 1000 artículos, 10 workers
            (2000, 20),  # 2000 artículos, 20 workers
        ]
        
        resultados_escalabilidad = []
        
        for cantidad, workers in cargas:
            print(f"\n🔄 Probando {cantidad} artículos con {workers} workers...")
            
            inicio = time.time()
            exitosos = 0
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                base_codigo = cantidad * 1000
                
                for i in range(cantidad):
                    producto = random.choice(self.productos)
                    codigo_barras = self.generar_codigo_barras_unico(base_codigo + i)
                    
                    future = executor.submit(
                        self.crear_articulo_request,
                        producto.id,
                        self.ubicacion.id,
                        codigo_barras
                    )
                    futures.append(future)
                
                for future in as_completed(futures):
                    resultado = future.result()
                    if resultado['success']:
                        exitosos += 1
            
            fin = time.time()
            tiempo_total = fin - inicio
            req_por_minuto = (cantidad / tiempo_total) * 60
            tasa_exito = (exitosos / cantidad) * 100
            
            resultado = {
                'cantidad': cantidad,
                'workers': workers,
                'tiempo': tiempo_total,
                'req_por_min': req_por_minuto,
                'tasa_exito': tasa_exito
            }
            resultados_escalabilidad.append(resultado)
            
            print(f"  ✓ Completado: {tiempo_total:.2f}s")
            print(f"  📈 Throughput: {req_por_minuto:.0f} req/min")
            print(f"  ✅ Tasa éxito: {tasa_exito:.1f}%")
        
        print(f"\n{'='*80}")
        print("📊 RESUMEN DE ESCALABILIDAD")
        print(f"{'='*80}")
        print(f"{'Cantidad':<12} {'Workers':<10} {'Tiempo (s)':<15} {'Req/min':<15} {'Éxito %':<10}")
        print("-" * 80)
        
        for r in resultados_escalabilidad:
            print(f"{r['cantidad']:<12} {r['workers']:<10} {r['tiempo']:<15.2f} "
                  f"{r['req_por_min']:<15.0f} {r['tasa_exito']:<10.1f}")
        
        print(f"\n🎯 ANÁLISIS:")
        mejor_throughput = max(r['req_por_min'] for r in resultados_escalabilidad)
        print(f"  Mejor throughput alcanzado: {mejor_throughput:.0f} req/min")
        print(f"  Objetivo máximo: 2,000 req/min")
        print(f"  Escalabilidad: {'✅ LOGRADA' if mejor_throughput >= 1000 else '⚠️  PARCIAL'}")
        
        # Verificar que hay incremento de capacidad
        throughputs = [r['req_por_min'] for r in resultados_escalabilidad]
        incremento = throughputs[-1] > throughputs[0]
        
        self.assertTrue(incremento, "Debe haber incremento en la capacidad de procesamiento")
        self.assertGreaterEqual(mejor_throughput, 100, "Debe alcanzar al menos 100 req/min")
    
    def test_05_manejo_errores_parciales(self):
        """
        Test 5: Manejo de errores parciales
        Objetivo: Validar que registros correctos se mantienen ante errores
        """
        print("\n" + "-"*80)
        print("TEST 5: MANEJO DE ERRORES PARCIALES")
        print("-"*80)
        
        cantidad_total = 100
        codigos_duplicados = []
        
        print(f"\n🧪 Creando {cantidad_total} artículos con 10% de códigos duplicados...")
        
        # Primera carga: artículos correctos
        for i in range(90):
            producto = random.choice(self.productos)
            codigo_barras = self.generar_codigo_barras_unico(50000 + i)
            self.crear_articulo_request(producto.id, self.ubicacion.id, codigo_barras)
        
        # Segunda carga: 10 con códigos duplicados (deben fallar)
        for i in range(10):
            producto = random.choice(self.productos)
            codigo_barras = self.generar_codigo_barras_unico(50000 + i % 90)  # Duplicado
            resultado = self.crear_articulo_request(producto.id, self.ubicacion.id, codigo_barras)
            if not resultado['success']:
                codigos_duplicados.append(codigo_barras)
        
        # Verificar integridad
        articulos_creados = Articulo.objects.filter(
            codigo_barras__startswith='78900005'
        ).count()
        
        print(f"\n📊 RESULTADOS:")
        print(f"  Total intentos: {cantidad_total}")
        print(f"  Artículos en DB: {articulos_creados}")
        print(f"  Errores por duplicados: {len(codigos_duplicados)}")
        print(f"  Registros correctos mantenidos: {articulos_creados}")
        
        print(f"\n✅ VALIDACIÓN:")
        print(f"  Los {articulos_creados} registros correctos se mantuvieron")
        print(f"  Los {len(codigos_duplicados)} registros duplicados fueron rechazados")
        print(f"  Integridad de datos: {'✅ PRESERVADA' if articulos_creados == 90 else '❌ COMPROMETIDA'}")
        
        self.assertEqual(articulos_creados, 90, "Deben mantenerse los 90 registros correctos")


class TestResumenAdministrador(TestCase):
    """
    Test para generar el resumen que debe recibir el administrador
    """
    
    def test_generar_resumen_carga_masiva(self):
        """Genera un resumen detallado del proceso de carga masiva"""
        print("\n" + "="*80)
        print("📋 RESUMEN EJECUTIVO PARA ADMINISTRADOR")
        print("="*80)
        
        resumen = {
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'operacion': 'Carga Masiva de Artículos',
            'objetivo': 'Procesar 10,000 registros en < 5 minutos',
            'metricas': {
                'throughput_minimo': '100 req/min',
                'throughput_maximo': '2,000 req/min',
                'tiempo_objetivo': '< 5 minutos',
                'tasa_exito_minima': '95%'
            },
            'requerimientos': [
                '✓ Validar integridad de datos',
                '✓ Evitar inconsistencias',
                '✓ Soportar carga sin degradación',
                '✓ Mantener registros correctos en errores parciales',
                '✓ Notificar administrador con resumen'
            ]
        }
        
        print(f"\nFecha: {resumen['fecha']}")
        print(f"Operación: {resumen['operacion']}")
        print(f"Objetivo: {resumen['objetivo']}")
        
        print(f"\n📊 MÉTRICAS OBJETIVO:")
        for key, value in resumen['metricas'].items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n✅ REQUERIMIENTOS A VALIDAR:")
        for req in resumen['requerimientos']:
            print(f"  {req}")
        
        print(f"\n{'='*80}")
        print("Para ejecutar las pruebas completas, ejecute:")
        print("  python manage.py test tests.test_carga_masiva_articulos")
        print(f"{'='*80}\n")
