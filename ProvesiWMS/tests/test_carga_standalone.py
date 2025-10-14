#!/usr/bin/env python3
"""
Script Standalone para Pruebas de Carga Masiva de Artículos

Script independiente que NO requiere Django test framework.
Usa solo bibliotecas estándar de Python + requests.

Instalación:
    pip install requests

Ejecución:
    python tests/test_carga_standalone.py

Pruebas disponibles:
    1. Baseline: 100 artículos secuenciales
    2. Concurrente: 1,000 artículos con 10 workers
    3. Objetivo principal: 10,000 artículos en < 5 minutos
    4. Escalabilidad: incremento de 100 a 2,000 req/min
    5. Errores parciales: manejo de fallos
"""

import time
import json
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal
import requests
from typing import Dict, List, Tuple


class ColoresTerminal:
    """Colores ANSI para output en terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PruebasCargaMasiva:
    """
    Clase principal para ejecutar pruebas de carga masiva
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.productos_ids = list(range(1, 52))  # IDs de productos (asumiendo que existen)
        self.ubicacion_id = 1  # ID de ubicación (asumiendo que existe)
        self.contador_codigos = 0
        self.session = requests.Session()
    
    def print_header(self, texto: str, color=ColoresTerminal.HEADER):
        """Imprime un encabezado con formato"""
        print(f"\n{color}{'='*80}")
        print(texto.center(80))
        print(f"{'='*80}{ColoresTerminal.END}\n")
    
    def print_seccion(self, texto: str):
        """Imprime una sección"""
        print(f"\n{ColoresTerminal.BLUE}{'-'*80}")
        print(texto)
        print(f"{'-'*80}{ColoresTerminal.END}")
    
    def generar_codigo_barras(self) -> str:
        """Genera un código de barras EAN-13 único"""
        self.contador_codigos += 1
        base = f"7898{self.contador_codigos:08d}"
        
        # Calcular dígito verificador EAN-13
        odd_sum = sum(int(base[i]) for i in range(0, 12, 2))
        even_sum = sum(int(base[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return base + str(check_digit)
    
    def crear_articulo(self, producto_id: int, ubicacion_id: int, codigo_barras: str) -> Dict:
        """Crea un artículo mediante POST request"""
        url = f"{self.base_url}/inventario/articulos/crear/"
        data = {
            'producto': producto_id,
            'codigo_barras': codigo_barras,
            'ubicacion': ubicacion_id
        }
        
        try:
            response = self.session.post(url, data=data, timeout=30)
            return {
                'success': response.status_code in [200, 302],
                'status_code': response.status_code,
                'codigo_barras': codigo_barras,
                'tiempo_respuesta': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'error': str(e),
                'codigo_barras': codigo_barras,
                'tiempo_respuesta': 0
            }
    
    def verificar_servidor(self) -> bool:
        """Verifica que el servidor esté disponible"""
        try:
            response = requests.get(f"{self.base_url}/inventario/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_01_baseline_100_articulos(self) -> Dict:
        """
        Test 1: Baseline - 100 artículos secuenciales
        Establece línea base de rendimiento
        """
        self.print_seccion("TEST 1: BASELINE - 100 ARTICULOS SECUENCIALES")
        
        cantidad = 100
        inicio = time.time()
        resultados = []
        
        print(f"Creando {cantidad} articulos secuencialmente...")
        
        for i in range(cantidad):
            if (i + 1) % 20 == 0:
                print(f"  Progreso: {i+1}/{cantidad} ({((i+1)/cantidad)*100:.0f}%)")
            
            producto_id = random.choice(self.productos_ids)
            codigo_barras = self.generar_codigo_barras()
            resultado = self.crear_articulo(producto_id, self.ubicacion_id, codigo_barras)
            resultados.append(resultado)
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        fallidos = cantidad - exitosos
        tasa_exito = (exitosos / cantidad) * 100
        req_por_segundo = cantidad / tiempo_total
        req_por_minuto = req_por_segundo * 60
        
        # Estadisticas de latencia
        tiempos = [r['tiempo_respuesta'] for r in resultados if r['tiempo_respuesta'] > 0]
        if tiempos:
            latencia_promedio = statistics.mean(tiempos) * 1000
            latencia_min = min(tiempos) * 1000
            latencia_max = max(tiempos) * 1000
        else:
            latencia_promedio = latencia_min = latencia_max = 0
        
        print(f"\n{ColoresTerminal.GREEN}RESULTADOS:")
        print(f"  Total articulos: {cantidad}")
        print(f"  Exitosos: {exitosos} ({tasa_exito:.2f}%)")
        print(f"  Fallidos: {fallidos}")
        print(f"  Tiempo total: {tiempo_total:.2f}s")
        print(f"  Latencia promedio: {latencia_promedio:.2f}ms")
        print(f"  Throughput: {req_por_segundo:.2f} req/s ({req_por_minuto:.0f} req/min)")
        print(f"{ColoresTerminal.END}")
        
        return {
            'test': 'baseline_100',
            'cantidad': cantidad,
            'exitosos': exitosos,
            'tiempo_total': tiempo_total,
            'req_por_minuto': req_por_minuto,
            'tasa_exito': tasa_exito,
            'latencia_promedio': latencia_promedio
        }
    
    def test_02_concurrente_1000_articulos(self, workers: int = 10) -> Dict:
        """
        Test 2: 1,000 artículos con concurrencia
        Prueba capacidad de procesamiento concurrente
        """
        self.print_seccion(f"TEST 2: CARGA CONCURRENTE - 1,000 ARTÍCULOS ({workers} WORKERS)")
        
        cantidad = 1000
        inicio = time.time()
        resultados = []
        tiempos_respuesta = []
        
        print(f"🚀 Creando {cantidad} artículos con {workers} workers concurrentes...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            for i in range(cantidad):
                producto_id = random.choice(self.productos_ids)
                codigo_barras = self.generar_codigo_barras()
                
                future = executor.submit(
                    self.crear_articulo,
                    producto_id,
                    self.ubicacion_id,
                    codigo_barras
                )
                futures.append((future, time.time()))
            
            completados = 0
            for future, tiempo_envio in futures:
                try:
                    resultado = future.result()
                    tiempo_respuesta = time.time() - tiempo_envio
                    tiempos_respuesta.append(tiempo_respuesta)
                    resultados.append(resultado)
                    
                    completados += 1
                    if completados % 100 == 0:
                        print(f"  Progreso: {completados}/{cantidad} ({(completados/cantidad)*100:.0f}%)")
                except Exception as e:
                    print(f"  ⚠️  Error: {str(e)}")
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        fallidos = cantidad - exitosos
        tasa_exito = (exitosos / cantidad) * 100
        req_por_segundo = cantidad / tiempo_total
        req_por_minuto = req_por_segundo * 60
        
        # Estadísticas de latencia
        if tiempos_respuesta:
            latencia_min = min(tiempos_respuesta) * 1000
            latencia_max = max(tiempos_respuesta) * 1000
            latencia_promedio = statistics.mean(tiempos_respuesta) * 1000
            latencia_p50 = statistics.median(tiempos_respuesta) * 1000
            latencia_p95 = statistics.quantiles(tiempos_respuesta, n=20)[18] * 1000
        else:
            latencia_min = latencia_max = latencia_promedio = latencia_p50 = latencia_p95 = 0
        
        print(f"\n{ColoresTerminal.GREEN}📊 RESULTADOS:")
        print(f"  ✓ Total artículos: {cantidad}")
        print(f"  ✓ Exitosos: {exitosos} ({tasa_exito:.2f}%)")
        print(f"  ✗ Fallidos: {fallidos}")
        print(f"  👥 Workers: {workers}")
        print(f"  ⏱️  Tiempo total: {tiempo_total:.2f}s")
        print(f"  📈 Throughput: {req_por_segundo:.2f} req/s ({req_por_minuto:.0f} req/min)")
        print(f"\n⚡ LATENCIAS:")
        print(f"  Min: {latencia_min:.2f}ms")
        print(f"  Max: {latencia_max:.2f}ms")
        print(f"  Promedio: {latencia_promedio:.2f}ms")
        print(f"  P50: {latencia_p50:.2f}ms")
        print(f"  P95: {latencia_p95:.2f}ms")
        print(f"{ColoresTerminal.END}")
        
        return {
            'test': 'concurrente_1000',
            'cantidad': cantidad,
            'workers': workers,
            'exitosos': exitosos,
            'tiempo_total': tiempo_total,
            'req_por_minuto': req_por_minuto,
            'tasa_exito': tasa_exito,
            'latencia_promedio': latencia_promedio,
            'latencia_p95': latencia_p95
        }
    
    def test_03_objetivo_10000_articulos(self, workers: int = 50) -> Dict:
        """
        Test 3: 10,000 artículos en menos de 5 minutos (OBJETIVO PRINCIPAL)
        Valida el requerimiento principal de carga masiva
        """
        self.print_seccion(f"TEST 3: OBJETIVO PRINCIPAL - 10,000 ARTÍCULOS (< 5 MIN)")
        
        cantidad = 10000
        workers = workers
        tiempo_objetivo = 300  # 5 minutos
        
        print(f"⚙️  CONFIGURACIÓN:")
        print(f"  Cantidad: {cantidad:,} artículos")
        print(f"  Workers: {workers}")
        print(f"  Tiempo objetivo: {tiempo_objetivo}s (5 minutos)")
        print(f"  Throughput requerido: {(cantidad/tiempo_objetivo)*60:.0f} req/min")
        
        input(f"\n{ColoresTerminal.YELLOW}⚠️  Esta prueba tomará varios minutos. Presione ENTER para continuar...{ColoresTerminal.END}")
        
        inicio = time.time()
        resultados = []
        tiempos_respuesta = []
        errores = []
        
        print(f"\n🚀 INICIANDO CARGA MASIVA DE {cantidad:,} ARTÍCULOS...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            for i in range(cantidad):
                producto_id = random.choice(self.productos_ids)
                codigo_barras = self.generar_codigo_barras()
                
                future = executor.submit(
                    self.crear_articulo,
                    producto_id,
                    self.ubicacion_id,
                    codigo_barras
                )
                futures.append((future, time.time(), codigo_barras))
            
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
                        porcentaje = (completados / cantidad) * 100
                        print(f"  ⏳ Progreso: {completados:,}/{cantidad:,} ({porcentaje:.1f}%) - "
                              f"{tasa_actual:.0f} req/min - "
                              f"Tiempo transcurrido: {tiempo_parcial:.0f}s")
                
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
            latencia_min = min(tiempos_respuesta) * 1000
            latencia_max = max(tiempos_respuesta) * 1000
            latencia_promedio = statistics.mean(tiempos_respuesta) * 1000
            latencia_p50 = statistics.median(tiempos_respuesta) * 1000
            latencia_p95 = statistics.quantiles(tiempos_respuesta, n=20)[18] * 1000
            latencia_p99 = statistics.quantiles(tiempos_respuesta, n=100)[98] * 1000
        else:
            latencia_min = latencia_max = latencia_promedio = latencia_p50 = latencia_p95 = latencia_p99 = 0
        
        self.print_header("📊 RESULTADOS FINALES - TEST OBJETIVO PRINCIPAL", ColoresTerminal.GREEN)
        
        print(f"✅ CARGA COMPLETADA:")
        print(f"  Total artículos: {cantidad:,}")
        print(f"  Exitosos: {exitosos:,} ({tasa_exito:.2f}%)")
        print(f"  Fallidos: {fallidos:,}")
        
        print(f"\n⏱️  TIEMPOS:")
        print(f"  Tiempo total: {tiempo_total:.2f}s ({tiempo_total/60:.2f} min)")
        print(f"  Tiempo objetivo: {tiempo_objetivo}s (5 min)")
        
        cumple_tiempo = tiempo_total <= tiempo_objetivo
        print(f"  {ColoresTerminal.GREEN}✅{ColoresTerminal.END if cumple_tiempo else ColoresTerminal.RED}❌{ColoresTerminal.END} "
              f"{'CUMPLE' if cumple_tiempo else 'NO CUMPLE'} el objetivo de tiempo")
        
        print(f"\n📈 THROUGHPUT:")
        print(f"  Requests/segundo: {req_por_segundo:.2f}")
        print(f"  Requests/minuto: {req_por_minuto:.0f}")
        print(f"  Objetivo mínimo: 100 req/min")
        print(f"  Objetivo máximo: 2,000 req/min")
        
        en_rango = 100 <= req_por_minuto <= 2000
        print(f"  {ColoresTerminal.GREEN if en_rango else ColoresTerminal.YELLOW}{'✅ DENTRO' if en_rango else '⚠️  FUERA'}{ColoresTerminal.END} "
              f"del rango objetivo")
        
        print(f"\n⚡ LATENCIAS:")
        print(f"  Min: {latencia_min:.2f}ms")
        print(f"  Max: {latencia_max:.2f}ms")
        print(f"  Promedio: {latencia_promedio:.2f}ms")
        print(f"  P50: {latencia_p50:.2f}ms")
        print(f"  P95: {latencia_p95:.2f}ms")
        print(f"  P99: {latencia_p99:.2f}ms")
        
        if errores:
            print(f"\n{ColoresTerminal.YELLOW}⚠️  ERRORES DETECTADOS ({len(errores)}):{ColoresTerminal.END}")
            for i, error in enumerate(errores[:5]):
                print(f"  {i+1}. Código: {error['codigo_barras']} - {error.get('error', 'Unknown')}")
            if len(errores) > 5:
                print(f"  ... y {len(errores)-5} errores más")
        
        # RESUMEN PARA ADMINISTRADOR
        self.print_header("📋 RESUMEN PARA ADMINISTRADOR", ColoresTerminal.CYAN)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Operación: Carga Masiva de Artículos")
        print(f"Registros procesados: {cantidad:,}")
        print(f"Registros exitosos: {exitosos:,}")
        print(f"Registros fallidos: {fallidos:,}")
        print(f"Tasa de éxito: {tasa_exito:.2f}%")
        print(f"Tiempo total: {tiempo_total/60:.2f} minutos")
        print(f"Throughput: {req_por_minuto:.0f} req/min")
        
        estado_final = "✅ EXITOSO" if (tasa_exito >= 95 and cumple_tiempo) else "⚠️  CON OBSERVACIONES"
        print(f"Estado: {estado_final}")
        print("="*80)
        
        return {
            'test': 'objetivo_10000',
            'cantidad': cantidad,
            'workers': workers,
            'exitosos': exitosos,
            'fallidos': fallidos,
            'tiempo_total': tiempo_total,
            'req_por_minuto': req_por_minuto,
            'tasa_exito': tasa_exito,
            'cumple_tiempo': cumple_tiempo,
            'cumple_tasa': tasa_exito >= 95,
            'latencia_promedio': latencia_promedio,
            'latencia_p95': latencia_p95,
            'latencia_p99': latencia_p99
        }
    
    def test_04_escalabilidad_incremental(self) -> List[Dict]:
        """
        Test 4: Escalabilidad incremental
        Valida que el sistema escala desde 100 req/min hasta 2000 req/min
        """
        self.print_seccion("TEST 4: ESCALABILIDAD INCREMENTAL (100 → 2000 req/min)")
        
        configuraciones = [
            (100, 2),    # 100 artículos, 2 workers
            (500, 5),    # 500 artículos, 5 workers
            (1000, 10),  # 1000 artículos, 10 workers
            (2000, 20),  # 2000 artículos, 20 workers
        ]
        
        resultados_escalabilidad = []
        
        for cantidad, workers in configuraciones:
            print(f"\n🔄 Probando {cantidad} artículos con {workers} workers...")
            
            inicio = time.time()
            exitosos = 0
            resultados = []
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                
                for i in range(cantidad):
                    producto_id = random.choice(self.productos_ids)
                    codigo_barras = self.generar_codigo_barras()
                    
                    future = executor.submit(
                        self.crear_articulo,
                        producto_id,
                        self.ubicacion_id,
                        codigo_barras
                    )
                    futures.append(future)
                
                for future in futures:
                    try:
                        resultado = future.result()
                        resultados.append(resultado)
                        if resultado['success']:
                            exitosos += 1
                    except:
                        pass
            
            fin = time.time()
            tiempo_total = fin - inicio
            req_por_minuto = (cantidad / tiempo_total) * 60
            tasa_exito = (exitosos / cantidad) * 100 if cantidad > 0 else 0
            
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
        
        print(f"\n{ColoresTerminal.GREEN}{'='*80}")
        print("📊 RESUMEN DE ESCALABILIDAD")
        print(f"{'='*80}{ColoresTerminal.END}")
        print(f"{'Cantidad':<12} {'Workers':<10} {'Tiempo (s)':<15} {'Req/min':<15} {'Éxito %':<10}")
        print("-" * 80)
        
        for r in resultados_escalabilidad:
            print(f"{r['cantidad']:<12} {r['workers']:<10} {r['tiempo']:<15.2f} "
                  f"{r['req_por_min']:<15.0f} {r['tasa_exito']:<10.1f}")
        
        mejor_throughput = max(r['req_por_min'] for r in resultados_escalabilidad)
        print(f"\n🎯 ANÁLISIS:")
        print(f"  Mejor throughput alcanzado: {mejor_throughput:.0f} req/min")
        print(f"  Objetivo máximo: 2,000 req/min")
        print(f"  Escalabilidad: {ColoresTerminal.GREEN}✅ LOGRADA{ColoresTerminal.END if mejor_throughput >= 1000 else ColoresTerminal.YELLOW}⚠️  PARCIAL{ColoresTerminal.END}")
        
        return resultados_escalabilidad
    
    def generar_reporte_json(self, resultados: List[Dict], filename: str = "reporte_carga_masiva.json"):
        """Genera un reporte en formato JSON"""
        reporte = {
            'fecha': datetime.now().isoformat(),
            'servidor': self.base_url,
            'resultados': resultados
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\n{ColoresTerminal.CYAN}📄 Reporte guardado en: {filename}{ColoresTerminal.END}")


def main():
    """Función principal"""
    print(f"""
{ColoresTerminal.HEADER}╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║          PRUEBAS DE CARGA MASIVA - SISTEMA DE INVENTARIO WMS                 ║
║                                                                                ║
║  Requerimiento Arquitecturalmente Significativo:                              ║
║  • Escalar de 100 req/min a 2,000 req/min                                    ║
║  • Procesar 10,000 registros en < 5 minutos                                  ║
║  • Validar integridad de datos                                                ║
║  • Mantener registros correctos en caso de errores parciales                 ║
║                                                                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝{ColoresTerminal.END}
""")
    
    # Configuración
    base_url = input(f"URL del servidor [{ColoresTerminal.CYAN}http://127.0.0.1:8000{ColoresTerminal.END}]: ").strip() or "http://127.0.0.1:8000"
    
    pruebas = PruebasCargaMasiva(base_url=base_url)
    
    # Verificar servidor
    print(f"\n🔍 Verificando conexión con el servidor...")
    if not pruebas.verificar_servidor():
        print(f"{ColoresTerminal.RED}❌ Error: No se puede conectar al servidor {base_url}{ColoresTerminal.END}")
        print(f"\n{ColoresTerminal.YELLOW}Asegúrese de que el servidor Django está corriendo:")
        print(f"  cd ProvesiWMS")
        print(f"  python manage.py runserver{ColoresTerminal.END}\n")
        sys.exit(1)
    
    print(f"{ColoresTerminal.GREEN}✅ Servidor disponible{ColoresTerminal.END}")
    
    # Menú de pruebas
    print(f"\n{ColoresTerminal.BOLD}SELECCIONE LAS PRUEBAS A EJECUTAR:{ColoresTerminal.END}")
    print("1. Test Baseline (100 artículos secuenciales) - ~30 segundos")
    print("2. Test Concurrente (1,000 artículos, 10 workers) - ~2 minutos")
    print("3. Test Objetivo Principal (10,000 artículos < 5 min) - ~5-10 minutos")
    print("4. Test Escalabilidad Incremental - ~10 minutos")
    print("5. Ejecutar TODAS las pruebas")
    print("0. Salir")
    
    opcion = input(f"\n{ColoresTerminal.YELLOW}Opción [1-5]: {ColoresTerminal.END}").strip()
    
    resultados = []
    
    try:
        if opcion == "1":
            resultado = pruebas.test_01_baseline_100_articulos()
            resultados.append(resultado)
        
        elif opcion == "2":
            resultado = pruebas.test_02_concurrente_1000_articulos()
            resultados.append(resultado)
        
        elif opcion == "3":
            resultado = pruebas.test_03_objetivo_10000_articulos()
            resultados.append(resultado)
        
        elif opcion == "4":
            resultados = pruebas.test_04_escalabilidad_incremental()
        
        elif opcion == "5":
            print(f"\n{ColoresTerminal.YELLOW}⚠️  TODAS LAS PRUEBAS - Esto tomará aproximadamente 20-30 minutos{ColoresTerminal.END}")
            confirmar = input("¿Continuar? [s/N]: ").strip().lower()
            if confirmar == 's':
                resultados.append(pruebas.test_01_baseline_100_articulos())
                resultados.append(pruebas.test_02_concurrente_1000_articulos())
                resultados.extend(pruebas.test_04_escalabilidad_incremental())
                resultados.append(pruebas.test_03_objetivo_10000_articulos())
        
        elif opcion == "0":
            print("Saliendo...")
            sys.exit(0)
        
        else:
            print(f"{ColoresTerminal.RED}Opción inválida{ColoresTerminal.END}")
            sys.exit(1)
        
        # Generar reporte
        if resultados:
            pruebas.generar_reporte_json(resultados)
        
        print(f"\n{ColoresTerminal.GREEN}✅ PRUEBAS COMPLETADAS EXITOSAMENTE{ColoresTerminal.END}\n")
    
    except KeyboardInterrupt:
        print(f"\n\n{ColoresTerminal.YELLOW}⚠️  Pruebas interrumpidas por el usuario{ColoresTerminal.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{ColoresTerminal.RED}❌ Error durante las pruebas: {str(e)}{ColoresTerminal.END}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
