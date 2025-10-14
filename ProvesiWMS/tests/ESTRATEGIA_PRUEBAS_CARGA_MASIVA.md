# Estrategia de Pruebas para Carga Masiva de Artículos

## 📋 Requerimiento Arquitecturalmente Significativo

**Objetivo**: Cuando realizo operaciones de carga masiva de inventario, el sistema debe:

1. ✅ Incrementar capacidad de procesamiento desde **100 req/min** hasta **2,000 req/min**
2. ✅ Procesar **10,000 registros** en menos de **5 minutos**
3. ✅ Validar integridad de datos
4. ✅ Evitar inconsistencias
5. ✅ Soportar la carga sin degradación
6. ✅ Mantener registros correctos en caso de errores parciales
7. ✅ Notificar al administrador con resumen del proceso

---

## 🎯 Enfoque de Pruebas

### Tipo de Pruebas: **Performance Testing / Load Testing / Stress Testing**

Se implementan 3 estrategias complementarias:

1. **Pruebas unitarias con Django** (`test_carga_masiva_articulos.py`)
2. **Pruebas de carga con Locust** (`locustfile_articulos.py`)
3. **Pruebas standalone con Python** (`test_carga_standalone.py`)

---

## 🧪 Suite de Pruebas Implementadas

### Test 1: Baseline (100 artículos secuenciales)
**Objetivo**: Establecer línea base de rendimiento

**Configuración**:
- Cantidad: 100 artículos
- Modo: Secuencial (sin concurrencia)
- Duración estimada: ~30 segundos

**Métricas a validar**:
- ✓ Tiempo de respuesta promedio < 1000ms
- ✓ Tasa de éxito > 95%
- ✓ Throughput baseline establecido

**Criterios de éxito**:
```python
assert tasa_exito > 95.0
assert tiempo_promedio < 1000  # ms
```

---

### Test 2: Carga Concurrente (1,000 artículos)
**Objetivo**: Validar procesamiento concurrente

**Configuración**:
- Cantidad: 1,000 artículos
- Workers concurrentes: 10
- Duración estimada: ~2 minutos

**Métricas a validar**:
- ✓ Throughput > 100 req/min
- ✓ Tasa de éxito > 95%
- ✓ P95 latencia < 3000ms
- ✓ No degradación de servicio

**Criterios de éxito**:
```python
assert req_por_minuto >= 100
assert tasa_exito >= 95.0
assert latencia_p95 < 3000  # ms
```

---

### Test 3: Objetivo Principal (10,000 artículos < 5 minutos)
**Objetivo**: **VALIDAR REQUERIMIENTO PRINCIPAL**

**Configuración**:
- Cantidad: 10,000 artículos
- Workers concurrentes: 50
- Tiempo objetivo: 300 segundos (5 minutos)
- Duración estimada: ~5-10 minutos

**Métricas críticas**:
- ✅ Tiempo total ≤ 300 segundos
- ✅ Throughput entre 100-2,000 req/min
- ✅ Tasa de éxito ≥ 95%
- ✅ Consistencia en DB ≥ 95%

**Criterios de éxito**:
```python
assert tiempo_total <= 300  # 5 minutos
assert 100 <= req_por_minuto <= 2000
assert tasa_exito >= 95.0
assert articulos_db >= exitosos * 0.95
```

**Resumen para administrador**:
```
Fecha: 2025-10-13 18:30:00
Operación: Carga Masiva de Artículos
Registros procesados: 10,000
Registros exitosos: 9,523
Registros fallidos: 477
Tasa de éxito: 95.23%
Tiempo total: 4.85 minutos
Throughput: 2,058 req/min
Estado: ✅ EXITOSO
```

---

### Test 4: Escalabilidad Incremental
**Objetivo**: Validar escalamiento de 100 a 2,000 req/min

**Configuración**:
Pruebas incrementales con cargas crecientes:

| Carga | Artículos | Workers | Throughput Esperado |
|-------|-----------|---------|-------------------|
| Baja | 100 | 2 | ~100-200 req/min |
| Media | 500 | 5 | ~400-600 req/min |
| Alta | 1,000 | 10 | ~800-1,200 req/min |
| Máxima | 2,000 | 20 | ~1,500-2,000 req/min |

**Métricas a validar**:
- ✓ Incremento lineal de throughput
- ✓ Mantener tasa de éxito > 95%
- ✓ Sin degradación en latencias

**Criterios de éxito**:
```python
throughputs = [r['req_por_min'] for r in resultados]
assert throughputs[-1] > throughputs[0]  # Incremento
assert max(throughputs) >= 1000  # Alcanza alta carga
```

---

### Test 5: Manejo de Errores Parciales
**Objetivo**: Validar resiliencia ante errores

**Configuración**:
- 90 artículos válidos
- 10 artículos con códigos duplicados (error esperado)

**Validaciones**:
- ✓ 90 registros correctos se mantienen en DB
- ✓ 10 registros duplicados son rechazados
- ✓ Integridad de datos preservada

**Criterios de éxito**:
```python
assert articulos_creados == 90
assert len(codigos_duplicados) == 10
# Los registros correctos NO se pierden por errores parciales
```

---

## 🛠️ Herramientas de Prueba

### 1. Django Tests (`python manage.py test`)
**Archivo**: `tests/test_carga_masiva_articulos.py`

```bash
# Ejecutar todas las pruebas
python manage.py test tests.test_carga_masiva_articulos

# Ejecutar prueba específica
python manage.py test tests.test_carga_masiva_articulos.TestCargaMasivaArticulos.test_03_carga_10000_articulos_objetivo_principal

# Con verbosidad
python manage.py test tests.test_carga_masiva_articulos -v 2
```

**Ventajas**:
- ✓ Integrado con Django ORM
- ✓ Transacciones automáticas
- ✓ Validación de integridad en DB

---

### 2. Locust (`locust -f locustfile_articulos.py`)
**Archivo**: `tests/locustfile_articulos.py`

**Instalación**:
```bash
pip install locust
```

**Ejecución - Interfaz Web**:
```bash
cd ProvesiWMS
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000
```
Abrir: http://localhost:8089

**Ejecución - Headless (automatizada)**:

```bash
# Baseline: 100 req/min
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000 \
       --users 2 --spawn-rate 1 --run-time 1m --headless

# Media carga: 500 req/min
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000 \
       --users 10 --spawn-rate 2 --run-time 2m --headless

# Alta carga: 1,000 req/min
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000 \
       --users 20 --spawn-rate 5 --run-time 3m --headless

# Objetivo: 10,000 artículos
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000 \
       --users 35 --spawn-rate 7 --run-time 5m --headless
```

**Ventajas**:
- ✓ Interfaz web con gráficos en tiempo real
- ✓ Estadísticas detalladas de latencia
- ✓ Distribución de usuarios realista
- ✓ Exportación de reportes CSV/HTML

---

### 3. Script Standalone (`python test_carga_standalone.py`)
**Archivo**: `tests/test_carga_standalone.py`

**Instalación**:
```bash
pip install requests
```

**Ejecución**:
```bash
cd ProvesiWMS
python tests/test_carga_standalone.py
```

**Menú interactivo**:
```
1. Test Baseline (100 artículos)
2. Test Concurrente (1,000 artículos)
3. Test Objetivo Principal (10,000 artículos)
4. Test Escalabilidad Incremental
5. Ejecutar TODAS las pruebas
```

**Ventajas**:
- ✓ No requiere Django test framework
- ✓ Menú interactivo
- ✓ Colores en terminal
- ✓ Reportes JSON automáticos
- ✓ Fácil de ejecutar

---

## 📊 Métricas Clave a Monitorear

### Métricas de Throughput
```
Requests por segundo (req/s)
Requests por minuto (req/min)
Tiempo total de procesamiento
```

### Métricas de Latencia
```
Latencia mínima (ms)
Latencia máxima (ms)
Latencia promedio (ms)
P50 - Mediana (ms)
P95 - Percentil 95 (ms)
P99 - Percentil 99 (ms)
```

### Métricas de Confiabilidad
```
Tasa de éxito (%)
Tasa de error (%)
Consistencia en DB (%)
```

### Métricas de Escalabilidad
```
Throughput vs Workers (gráfico)
Latencia vs Carga (gráfico)
Error rate vs Carga (gráfico)
```

---

## 🎯 Criterios de Aceptación

### Criterio 1: Throughput
```
✅ Throughput mínimo: 100 req/min
✅ Throughput máximo: 2,000 req/min
✅ Sistema debe escalar gradualmente entre ambos
```

### Criterio 2: Tiempo de Procesamiento
```
✅ 10,000 artículos en ≤ 300 segundos (5 minutos)
```

### Criterio 3: Confiabilidad
```
✅ Tasa de éxito ≥ 95%
✅ Consistencia en DB ≥ 95%
```

### Criterio 4: Latencia
```
✅ Latencia P95 ≤ 3000ms bajo carga normal
✅ Latencia P99 ≤ 5000ms bajo carga máxima
```

### Criterio 5: Resiliencia
```
✅ Mantener registros correctos ante errores parciales
✅ No rollback de transacciones exitosas
✅ Notificación de errores al administrador
```

---

## 🚀 Plan de Ejecución

### Fase 1: Preparación (5 min)
1. Iniciar servidor Django
```bash
cd ProvesiWMS
python manage.py runserver
```

2. Verificar datos base (productos, ubicaciones)
```bash
python manage.py shell
>>> from inventario.models import Producto, UbicacionBodega
>>> Producto.objects.count()
51
>>> UbicacionBodega.objects.count()
1
```

### Fase 2: Pruebas Básicas (5 min)
```bash
# Test baseline
python tests/test_carga_standalone.py
# Opción 1: Baseline
```

### Fase 3: Pruebas de Carga (10 min)
```bash
# Test concurrente
python tests/test_carga_standalone.py
# Opción 2: Concurrente 1,000
```

### Fase 4: Prueba Objetivo (10 min)
```bash
# Test 10,000 artículos
python tests/test_carga_standalone.py
# Opción 3: Objetivo Principal
```

### Fase 5: Análisis de Resultados (10 min)
- Revisar reportes JSON generados
- Analizar métricas vs criterios de aceptación
- Documentar observaciones

---

## 📈 Ejemplo de Reporte Esperado

```json
{
  "fecha": "2025-10-13T18:30:00",
  "servidor": "http://127.0.0.1:8000",
  "resultados": [
    {
      "test": "objetivo_10000",
      "cantidad": 10000,
      "workers": 50,
      "exitosos": 9523,
      "fallidos": 477,
      "tiempo_total": 291.5,
      "req_por_minuto": 2058,
      "tasa_exito": 95.23,
      "cumple_tiempo": true,
      "cumple_tasa": true,
      "latencia_promedio": 145.3,
      "latencia_p95": 892.1,
      "latencia_p99": 1453.7
    }
  ]
}
```

---

## ✅ Checklist de Validación

- [ ] Sistema procesa 10,000 artículos en < 5 minutos
- [ ] Throughput entre 100 y 2,000 req/min
- [ ] Tasa de éxito ≥ 95%
- [ ] Latencia P95 ≤ 3000ms
- [ ] Registros correctos se mantienen ante errores
- [ ] Integridad de datos validada
- [ ] Resumen generado para administrador
- [ ] Sin degradación de servicio bajo carga

---

## 🔧 Troubleshooting

### Problema: Throughput muy bajo
**Solución**: Aumentar workers concurrentes

### Problema: Muchos errores de conexión
**Solución**: Verificar límites del servidor (max connections)

### Problema: Inconsistencias en DB
**Solución**: Revisar transacciones y manejo de errores

### Problema: Timeout en requests
**Solución**: Aumentar timeout en configuración (default: 30s)

---

## 📚 Referencias

- Django Performance Testing: https://docs.djangoproject.com/en/4.2/topics/testing/advanced/
- Locust Documentation: https://docs.locust.io/
- Python concurrent.futures: https://docs.python.org/3/library/concurrent.futures.html

---

## 👥 Equipo y Responsabilidades

**QA Engineer**: Ejecutar pruebas y documentar resultados  
**DevOps Engineer**: Monitorear recursos del servidor  
**Backend Developer**: Optimizar endpoints si es necesario  
**Product Owner**: Validar criterios de aceptación

---

**Última actualización**: 2025-10-13  
**Versión**: 1.0  
**Estado**: ✅ Listo para ejecución
