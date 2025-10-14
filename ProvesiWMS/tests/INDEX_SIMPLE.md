# Index - Pruebas de Carga Masiva

## Inicio Rapido

**Ejecutar esto primero:**

```bash
# Terminal 1
python manage.py runserver

# Terminal 2
python tests/test_carga_simple.py
# Seleccionar: 3
```

## Estructura de Archivos

### Scripts (Ejecutables)
```
test_carga_simple.py              [RECOMENDADO] Script standalone
test_carga_masiva_articulos.py    Tests Django para CI/CD
locustfile_articulos.py            Tests Locust con interfaz web
```

### Documentacion (Leer)
```
README_TESTS.md                   README principal
README_SIMPLE.md                  Guia rapida de comandos
RESUMEN_FINAL_SIMPLE.md          Resumen de implementacion
INDEX.md                          Este archivo
```

### Documentacion Detallada (Referencia)
```
RESUMEN_EJECUTIVO.md              Estrategia completa
ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md    Detalles tecnicos
IMPLEMENTACION_COMPLETA.md        Implementacion original (con emojis)
```

## Por Donde Empezar

### Primera vez
1. Leer `README_TESTS.md` (2 min)
2. Ejecutar `test_carga_simple.py` opcion 1 (30 seg)
3. Revisar resultados

### Validar requerimiento
1. Leer `README_SIMPLE.md` (2 min)
2. Ejecutar `test_carga_simple.py` opcion 3 (5 min)
3. Verificar `reporte_carga.json`

### Analisis profundo
1. Leer `RESUMEN_EJECUTIVO.md` (10 min)
2. Ejecutar `test_carga_simple.py` opcion 5 (30 min)
3. Analizar metricas detalladas

## Tests Rapidos

### Test 1: Baseline (30 segundos)
```bash
python tests/test_carga_simple.py
# Opcion: 1
```

### Test 3: Objetivo Principal (5 minutos)
```bash
python tests/test_carga_simple.py
# Opcion: 3
```

## Comandos por Herramienta

### Script Simple
```bash
python tests/test_carga_simple.py
```

### Tests Django
```bash
python manage.py test tests.test_carga_masiva_articulos
```

### Locust
```bash
pip install locust
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000
```

## Requerimiento a Validar

- Procesar 10,000 articulos en < 5 minutos
- Throughput: 100 - 2,000 req/min
- Tasa de exito: >= 95%
- Integridad de datos: >= 95%

## Archivos de Salida

- `reporte_carga.json` - Resultados automaticos

## Flujo Recomendado

```
1. Leer README_TESTS.md
   └─> Entender estructura (2 min)

2. Leer README_SIMPLE.md
   └─> Ver comandos (2 min)

3. Ejecutar test_carga_simple.py opcion 3
   └─> Validar requerimiento (5 min)

4. Revisar reporte_carga.json
   └─> Analizar resultados (2 min)

5. (Opcional) Leer documentacion detallada
   └─> Profundizar (segun necesidad)
```

## Troubleshooting Rapido

### Servidor no responde
```bash
python manage.py runserver
```

### Falta requests
```bash
pip install requests
```

### Pruebas lentas
- Reducir workers
- Verificar carga sistema
- Revisar base de datos

## Ayuda por Rol

### QA Engineer
- Archivo: `test_carga_simple.py`
- Documentacion: `README_SIMPLE.md`

### DevOps
- Archivo: `test_carga_masiva_articulos.py`
- Documentacion: `ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md`

### Product Owner
- Archivo: `reporte_carga.json` (resultados)
- Documentacion: `RESUMEN_EJECUTIVO.md`

### Developer
- Archivo: Cualquier script
- Documentacion: Todos los archivos

## Resumen

**Archivos totales**: 10
**Scripts ejecutables**: 3
**Documentacion**: 7
**Tiempo para validar requerimiento**: 10 minutos

**Estado**: COMPLETO Y LISTO

---

**Siguiente paso**: `python tests/test_carga_simple.py` (opcion 3)
