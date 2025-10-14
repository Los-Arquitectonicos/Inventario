#!/usr/bin/env python3
"""
Script Simple para Pruebas de Carga Masiva de Articulos

Script independiente que NO requiere Django test framework.

Instalacion:
    pip install requests

Ejecucion:
    python tests/test_carga_simple.py
"""

import time
import json
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import requests
from typing import Dict, List


class PruebasCargaMasiva:
    """Clase principal para ejecutar pruebas de carga masiva"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.productos_ids = list(range(1, 52))
        self.ubicacion_id = 1
        self.contador_codigos = 0
        self.session = requests.Session()
    
    def generar_codigo_barras(self) -> str:
        """Genera un codigo de barras EAN-13 unico"""
        self.contador_codigos += 1
        base = f"7898{self.contador_codigos:08d}"
        
        # Calcular digito verificador EAN-13
        odd_sum = sum(int(base[i]) for i in range(0, 12, 2))
        even_sum = sum(int(base[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return base + str(check_digit)
    
    def crear_articulo(self, producto_id: int, ubicacion_id: int, codigo_barras: str, use_new_session: bool = False) -> Dict:
        """Crea un articulo mediante POST request
        
        Args:
            producto_id: ID del producto
            ubicacion_id: ID de la ubicacion
            codigo_barras: Codigo de barras del articulo
            use_new_session: Si es True, crea una nueva sesion para thread-safety
        """
        url = f"{self.base_url}/inventario/articulos/crear/"
        data = {
            'producto_id': producto_id,
            'codigo_barras': codigo_barras,
            'ubicacion_id': ubicacion_id
        }
        
        try:
            # Para concurrencia, usar una sesion nueva (thread-safe)
            if use_new_session:
                session = requests.Session()
                response = session.post(url, json=data, timeout=30)
                session.close()
            else:
                # Para tests secuenciales, reutilizar la sesion
                response = self.session.post(url, json=data, timeout=30)
            
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
        """Verifica que el servidor este disponible"""
        try:
            response = requests.get(f"{self.base_url}/inventario/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_baseline_100(self) -> Dict:
        """Test 1: 100 articulos secuenciales"""
        print("\n" + "="*80)
        print("TEST 1: BASELINE - 100 ARTICULOS")
        print("="*80)
        
        cantidad = 100
        inicio = time.time()
        resultados = []
        
        print(f"\nCreando {cantidad} articulos...")
        
        for i in range(cantidad):
            if (i + 1) % 20 == 0:
                print(f"Progreso: {i+1}/{cantidad}")
            
            producto_id = random.choice(self.productos_ids)
            codigo_barras = self.generar_codigo_barras()
            resultado = self.crear_articulo(producto_id, self.ubicacion_id, codigo_barras)
            resultados.append(resultado)
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        tasa_exito = (exitosos / cantidad) * 100
        req_por_minuto = (cantidad / tiempo_total) * 60
        
        tiempos = [r['tiempo_respuesta'] for r in resultados if r['tiempo_respuesta'] > 0]
        latencia_promedio = statistics.mean(tiempos) * 1000 if tiempos else 0
        
        print(f"\nRESULTADOS:")
        print(f"  Total: {cantidad}")
        print(f"  Exitosos: {exitosos} ({tasa_exito:.1f}%)")
        print(f"  Tiempo: {tiempo_total:.1f}s")
        print(f"  Latencia: {latencia_promedio:.0f}ms")
        print(f"  Throughput: {req_por_minuto:.0f} req/min")
        
        return {
            'test': 'baseline_100',
            'cantidad': cantidad,
            'exitosos': exitosos,
            'tiempo_total': tiempo_total,
            'req_por_minuto': req_por_minuto,
            'tasa_exito': tasa_exito
        }
    
    def test_concurrente_1000(self, workers: int = 10) -> Dict:
        """Test 2: 1,000 articulos con concurrencia"""
        print("\n" + "="*80)
        print(f"TEST 2: CONCURRENTE - 1,000 ARTICULOS ({workers} workers)")
        print("="*80)
        
        cantidad = 1000
        inicio = time.time()
        resultados = []
        tiempos_respuesta = []
        
        print(f"\nCreando {cantidad} articulos con {workers} workers...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            for i in range(cantidad):
                producto_id = random.choice(self.productos_ids)
                codigo_barras = self.generar_codigo_barras()
                
                future = executor.submit(
                    self.crear_articulo,
                    producto_id,
                    self.ubicacion_id,
                    codigo_barras,
                    True  # use_new_session=True para thread-safety
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
                    if completados % 200 == 0:
                        print(f"Progreso: {completados}/{cantidad}")
                except Exception as e:
                    print(f"Error: {str(e)}")
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        tasa_exito = (exitosos / cantidad) * 100
        req_por_minuto = (cantidad / tiempo_total) * 60
        
        if tiempos_respuesta:
            latencia_promedio = statistics.mean(tiempos_respuesta) * 1000
            latencia_p95 = statistics.quantiles(tiempos_respuesta, n=20)[18] * 1000
        else:
            latencia_promedio = latencia_p95 = 0
        
        print(f"\nRESULTADOS:")
        print(f"  Total: {cantidad}")
        print(f"  Exitosos: {exitosos} ({tasa_exito:.1f}%)")
        print(f"  Workers: {workers}")
        print(f"  Tiempo: {tiempo_total:.1f}s")
        print(f"  Throughput: {req_por_minuto:.0f} req/min")
        print(f"  Latencia promedio: {latencia_promedio:.0f}ms")
        print(f"  Latencia P95: {latencia_p95:.0f}ms")
        
        return {
            'test': 'concurrente_1000',
            'cantidad': cantidad,
            'workers': workers,
            'exitosos': exitosos,
            'tiempo_total': tiempo_total,
            'req_por_minuto': req_por_minuto,
            'tasa_exito': tasa_exito
        }
    
    def test_objetivo_10000(self, workers: int = 50) -> Dict:
        """Test 3: 10,000 articulos - OBJETIVO PRINCIPAL"""
        print("\n" + "="*80)
        print("TEST 3: OBJETIVO PRINCIPAL - 10,000 ARTICULOS")
        print("="*80)
        
        cantidad = 10000
        tiempo_objetivo = 300  # 5 minutos
        
        print(f"\nConfiguracion:")
        print(f"  Cantidad: {cantidad:,} articulos")
        print(f"  Workers: {workers}")
        print(f"  Tiempo objetivo: {tiempo_objetivo}s (5 min)")
        
        respuesta = input("\nPresione ENTER para continuar...")
        
        inicio = time.time()
        resultados = []
        tiempos_respuesta = []
        
        print(f"\nIniciando carga masiva...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            
            for i in range(cantidad):
                producto_id = random.choice(self.productos_ids)
                codigo_barras = self.generar_codigo_barras()
                
                future = executor.submit(
                    self.crear_articulo,
                    producto_id,
                    self.ubicacion_id,
                    codigo_barras,
                    True  # use_new_session=True para thread-safety
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
                    if completados % 1000 == 0:
                        tiempo_parcial = time.time() - inicio
                        tasa_actual = (completados / tiempo_parcial) * 60
                        print(f"Progreso: {completados:,}/{cantidad:,} ({(completados/cantidad)*100:.0f}%) - "
                              f"{tasa_actual:.0f} req/min - {tiempo_parcial:.0f}s")
                
                except Exception as e:
                    pass
        
        fin = time.time()
        tiempo_total = fin - inicio
        
        exitosos = sum(1 for r in resultados if r['success'])
        fallidos = cantidad - exitosos
        tasa_exito = (exitosos / cantidad) * 100
        req_por_minuto = (cantidad / tiempo_total) * 60
        
        if tiempos_respuesta:
            latencia_promedio = statistics.mean(tiempos_respuesta) * 1000
            latencia_p95 = statistics.quantiles(tiempos_respuesta, n=20)[18] * 1000
            latencia_p99 = statistics.quantiles(tiempos_respuesta, n=100)[98] * 1000
        else:
            latencia_promedio = latencia_p95 = latencia_p99 = 0
        
        cumple_tiempo = tiempo_total <= tiempo_objetivo
        cumple_tasa = tasa_exito >= 95
        
        print(f"\n" + "="*80)
        print("RESULTADOS FINALES")
        print("="*80)
        print(f"\nCarga:")
        print(f"  Total: {cantidad:,}")
        print(f"  Exitosos: {exitosos:,} ({tasa_exito:.1f}%)")
        print(f"  Fallidos: {fallidos:,}")
        
        print(f"\nTiempos:")
        print(f"  Total: {tiempo_total:.1f}s ({tiempo_total/60:.1f} min)")
        print(f"  Objetivo: {tiempo_objetivo}s (5 min)")
        print(f"  Cumple: {'SI' if cumple_tiempo else 'NO'}")
        
        print(f"\nThroughput:")
        print(f"  Req/min: {req_por_minuto:.0f}")
        print(f"  Rango objetivo: 100 - 2,000")
        print(f"  En rango: {'SI' if 100 <= req_por_minuto <= 2000 else 'NO'}")
        
        print(f"\nLatencias:")
        print(f"  Promedio: {latencia_promedio:.0f}ms")
        print(f"  P95: {latencia_p95:.0f}ms")
        print(f"  P99: {latencia_p99:.0f}ms")
        
        print(f"\n" + "="*80)
        print("RESUMEN PARA ADMINISTRADOR")
        print("="*80)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Operacion: Carga Masiva de Articulos")
        print(f"Registros procesados: {cantidad:,}")
        print(f"Registros exitosos: {exitosos:,}")
        print(f"Tasa de exito: {tasa_exito:.1f}%")
        print(f"Tiempo total: {tiempo_total/60:.1f} minutos")
        print(f"Throughput: {req_por_minuto:.0f} req/min")
        print(f"Estado: {'EXITOSO' if (cumple_tiempo and cumple_tasa) else 'CON OBSERVACIONES'}")
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
            'cumple_tasa': cumple_tasa,
            'latencia_promedio': latencia_promedio,
            'latencia_p95': latencia_p95,
            'latencia_p99': latencia_p99
        }
    
    def test_escalabilidad(self) -> List[Dict]:
        """Test 4: Escalabilidad incremental"""
        print("\n" + "="*80)
        print("TEST 4: ESCALABILIDAD INCREMENTAL")
        print("="*80)
        
        configuraciones = [
            (100, 2),
            (500, 5),
            (1000, 10),
            (2000, 20),
        ]
        
        resultados_escalabilidad = []
        
        for cantidad, workers in configuraciones:
            print(f"\nProbando {cantidad} articulos con {workers} workers...")
            
            inicio = time.time()
            exitosos = 0
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                
                for i in range(cantidad):
                    producto_id = random.choice(self.productos_ids)
                    codigo_barras = self.generar_codigo_barras()
                    
                    future = executor.submit(
                        self.crear_articulo,
                        producto_id,
                        self.ubicacion_id,
                        codigo_barras,
                        True  # use_new_session=True para thread-safety
                    )
                    futures.append(future)
                
                for future in futures:
                    try:
                        resultado = future.result()
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
            
            print(f"  Tiempo: {tiempo_total:.1f}s")
            print(f"  Throughput: {req_por_minuto:.0f} req/min")
            print(f"  Exito: {tasa_exito:.1f}%")
        
        print(f"\n" + "="*80)
        print("RESUMEN DE ESCALABILIDAD")
        print("="*80)
        print(f"\n{'Cantidad':<12} {'Workers':<10} {'Tiempo':<12} {'Req/min':<12} {'Exito %':<10}")
        print("-" * 80)
        
        for r in resultados_escalabilidad:
            print(f"{r['cantidad']:<12} {r['workers']:<10} {r['tiempo']:<12.1f} "
                  f"{r['req_por_min']:<12.0f} {r['tasa_exito']:<10.1f}")
        
        mejor_throughput = max(r['req_por_min'] for r in resultados_escalabilidad)
        print(f"\nMejor throughput: {mejor_throughput:.0f} req/min")
        print(f"Objetivo maximo: 2,000 req/min")
        
        return resultados_escalabilidad
    
    def generar_reporte_json(self, resultados: List[Dict], filename: str = "reporte_carga.json"):
        """Genera reporte en JSON"""
        reporte = {
            'fecha': datetime.now().isoformat(),
            'servidor': self.base_url,
            'resultados': resultados
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\nReporte guardado en: {filename}")


def main():
    """Funcion principal"""
    print("""
===============================================================================
        PRUEBAS DE CARGA MASIVA - SISTEMA DE INVENTARIO WMS
===============================================================================

Requerimiento:
  - Escalar de 100 req/min a 2,000 req/min
  - Procesar 10,000 registros en < 5 minutos
  - Validar integridad de datos

===============================================================================
""")
    
    base_url = input(f"URL del servidor [http://127.0.0.1:8000]: ").strip() or "http://127.0.0.1:8000"
    
    pruebas = PruebasCargaMasiva(base_url=base_url)
    
    # Verificar servidor
    print(f"\nVerificando conexion con el servidor...")
    if not pruebas.verificar_servidor():
        print(f"ERROR: No se puede conectar al servidor {base_url}")
        print(f"\nAsegurese de que el servidor Django esta corriendo:")
        print(f"  cd ProvesiWMS")
        print(f"  python manage.py runserver\n")
        sys.exit(1)
    
    print(f"Servidor disponible")
    
    # Menu de pruebas
    print(f"\nSELECCIONE LA PRUEBA:")
    print("1. Test Baseline (100 articulos) - 30 seg")
    print("2. Test Concurrente (1,000 articulos) - 2 min")
    print("3. Test Objetivo Principal (10,000 articulos) - 5 min")
    print("4. Test Escalabilidad - 10 min")
    print("5. Ejecutar todas las pruebas")
    print("0. Salir")
    
    opcion = input(f"\nOpcion [1-5]: ").strip()
    
    resultados = []
    
    try:
        if opcion == "1":
            resultado = pruebas.test_baseline_100()
            resultados.append(resultado)
        
        elif opcion == "2":
            resultado = pruebas.test_concurrente_1000()
            resultados.append(resultado)
        
        elif opcion == "3":
            resultado = pruebas.test_objetivo_10000()
            resultados.append(resultado)
        
        elif opcion == "4":
            resultados = pruebas.test_escalabilidad()
        
        elif opcion == "5":
            print(f"\nTodas las pruebas - Esto tomara aproximadamente 20-30 minutos")
            confirmar = input("Continuar? [s/N]: ").strip().lower()
            if confirmar == 's':
                resultados.append(pruebas.test_baseline_100())
                resultados.append(pruebas.test_concurrente_1000())
                resultados.extend(pruebas.test_escalabilidad())
                resultados.append(pruebas.test_objetivo_10000())
        
        elif opcion == "0":
            print("Saliendo...")
            sys.exit(0)
        
        else:
            print("Opcion invalida")
            sys.exit(1)
        
        # Generar reporte
        if resultados:
            pruebas.generar_reporte_json(resultados)
        
        print(f"\nPRUEBAS COMPLETADAS\n")
    
    except KeyboardInterrupt:
        print(f"\n\nPruebas interrumpidas por el usuario\n")
        sys.exit(1)
    except Exception as e:
        print(f"\nError durante las pruebas: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
