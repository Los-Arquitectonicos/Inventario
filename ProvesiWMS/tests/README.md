# Pruebas de Carga - Sistema de Inventario WMS

## ASR escalabilidad

Yo, como personal administrativo de Provesi, dado que el ambiente está sobrecargado con la apertura de nuevas bodegas, cuando realizo operaciones de carga masiva de inventario, quiero que el sistema incremente su capacidad de procesamiento desde 100 peticiones por minuto hasta 2.000 peticiones por minuto, asegurando que cada carga de 10.000 registros se complete en menos de 5 minutos conforme crece la demanda.

## Resumen

Pruebas automatizadas con Locust para validar el requerimiento de escalabilidad del sistema:
- Throughput: 100 a 2,000 peticiones/minuto
- Capacidad: 10,000 registros en menos de 5 minutos
- Tasa de exito: >= 95%

## Estructura de Archivos

```
tests/
├── locustfile.py          # Definicion de pruebas de carga
├── config_entornos.py     # Configuracion (URL, timeouts)
├── run_load_tests.sh      # Script de ejecucion automatizada
└── reportes/              # Reportes HTML/CSV generados
```

## Configuracion Inicial

### 1. Instalar Locust

```bash
pip install locust
```

### 2. Preparar Datos en AWS

Genera la coleccion Postman con todos los datos necesarios:

```bash
cd scripts_llenar_db
python generar_postman_datos_completos.py
```

Importa `postman_datos_completos.json` en Postman y ejecuta la coleccion.

**Configuracion recomendada:**
- Delay entre requests: 100ms
- Tiempo estimado: 2 minutos

**Datos creados:**
- 50 productos
- 10 bodegas (diferentes ciudades)
- 1,000 ubicaciones (100 por bodega, capacidad 1M cada una)
- Capacidad total: 1,000,000,000 articulos

### 3. Configurar URL del Servidor

Edita `tests/config_entornos.py`:

```python
BASE_URL = "http://provesi-alb-xxxx.us-east-1.elb.amazonaws.com/inventario/"
TIMEOUT = 30
```


## Ejecutar Pruebas

### Pruebas Automatizadas

```bash
# Baseline: 100 req/min
./tests/run_load_tests.sh baseline

# Media: 500 req/min
./tests/run_load_tests.sh medium

# Alta: 1,000 req/min
./tests/run_load_tests.sh high

# Maxima: 2,000 req/min
./tests/run_load_tests.sh max

# Objetivo: 10,000 articulos
./tests/run_load_tests.sh objective

# Todas las pruebas
./tests/run_load_tests.sh all
```

### Interfaz Web (Opcional)

```bash
./tests/run_load_tests.sh web
```

Abre http://localhost:8089 y configura manualmente.

## Perfiles de Prueba

| Perfil | Usuarios | Spawn Rate | Duracion | Throughput Esperado | Articulos Creados |
|--------|----------|------------|----------|---------------------|-------------------|
| baseline | 2 | 1/seg | 1 min | ~100 req/min | ~100 |
| medium | 10 | 2/seg | 2 min | ~500 req/min | ~1,000 |
| high | 20 | 5/seg | 3 min | ~1,000 req/min | ~3,000 |
| max | 40 | 10/seg | 5 min | ~2,000 req/min | ~10,000 |
| objective | 35 | 7/seg | 5 min | ~2,000 req/min | ~10,000 |

**Parametros explicados:**
- **Usuarios**: Cantidad de usuarios virtuales simultaneos
- **Spawn Rate**: Velocidad de inicio de usuarios (usuarios/segundo)
- **Duracion**: Tiempo total de ejecucion de la prueba
- **Throughput**: Peticiones por minuto esperadas


## Interpretar Resultados

### Reportes Generados

Cada prueba genera automaticamente un reporte JSON en la carpeta `reportes/`:

**Formato:** `reportes/reporte_[perfil]_[timestamp].json`

**Ejemplos:**
- `reportes/reporte_baseline_20251015_143022.json`
- `reportes/reporte_objective_20251015_143500.json`

El reporte JSON incluye metricas completas con evaluacion automatica de objetivos.

### Metricas Principales

El reporte JSON contiene:

**Request Statistics:**
- `total_requests`: Total de peticiones enviadas
- `exitosos`: Peticiones exitosas
- `fallidos`: Peticiones fallidas
- `tasa_exito_pct`: Porcentaje de exito
- `req_por_minuto`: Throughput (peticiones por minuto)

**Response Time:**
- `response_time_avg_ms`: Tiempo de respuesta promedio
- `response_time_p50_ms`: Percentil 50 (mediana)
- `response_time_p95_ms`: Percentil 95
- `response_time_p99_ms`: Percentil 99

**Objetivos Evaluados:**
```json
{
  "objetivos": {
    "throughput_min_100": true,      // >= 100 req/min
    "throughput_max_2000": true,     // <= 2,000 req/min
    "tiempo_10k_menos_5min": true,   // 10k articulos en <5 min
    "tasa_exito_95pct": true         // >= 95% exitosos
  }
}
```

### Criterios de Exito

| Metrica | Objetivo | Critico |
|---------|----------|---------|
| Throughput minimo | >= 100 req/min | Si |
| Throughput maximo | <= 2,000 req/min | Si |
| Tasa de exito | >= 95% | Si |
| Tiempo 10k articulos | < 5 min | Si |
| P95 tiempo respuesta | < 500ms | No |
| P99 tiempo respuesta | < 1000ms | No |


## Distribucion y Unicidad

### Distribucion entre Ubicaciones

Las pruebas distribuyen automaticamente los articulos entre todas las ubicaciones disponibles:

```python
# Al inicio, las pruebas consultan todas las ubicaciones
ubicaciones_url = f"{BASE_URL}/api/ubicaciones/?limit=2000"

# Cada articulo se asigna aleatoriamente
ubicacion_id = random.choice(UBICACION_IDS)
```

Con 1,000 ubicaciones, cada una recibe aproximadamente 10 articulos en la prueba objective (10,000 articulos).

### Codigos de Barras Unicos

Los codigos EAN-13 se generan con timestamp en microsegundos:

```python
timestamp = int(time.time() * 1000000) % 1000000
codigo = timestamp * 1000 + contador
```

Esto permite ejecutar las pruebas multiples veces sin conflictos de codigos duplicados.

## Limpieza de Datos (Opcional)

### Opcion 1: Comando Django (Solo Articulos)

Elimina articulos creados durante las pruebas:

```bash
python manage.py limpiar_articulos --all --yes
```

### Opcion 2: Coleccion Postman (Limpieza Completa)

Para eliminar todos los datos (productos, bodegas, ubicaciones, articulos):

```bash
cd scripts_llenar_db
python generar_postman_limpiar_datos.py
```

Importa `postman_limpiar_datos.json` en Postman y ejecuta la coleccion.

**NOTA:** Requiere implementar endpoints de eliminacion masiva en el backend:
- `DELETE /api/articulos/eliminar_todos/`
- `DELETE /api/ubicaciones/eliminar_todas/`
- `DELETE /api/bodegas/eliminar_todas/`
- `DELETE /api/productos/eliminar_todos/`

## Arquitectura AWS

```
Application Load Balancer (puerto 80)
    |
    ├── EC2 App Server 1 (Django + Gunicorn)
    ├── EC2 App Server 2 (Django + Gunicorn)
    |
    └── EC2 Database Server (PostgreSQL 16)
```

**Configuracion:**
- Base de datos: PostgreSQL 16
- Servidor web: Gunicorn
- Balanceador: AWS Application Load Balancer
- Capacidad: 2 servidores de aplicacion

## Configuracion Avanzada

### Variables de Entorno

```bash
export BASE_URL="http://otro-servidor.com/inventario/"
export TIMEOUT="60"

./tests/run_load_tests.sh objective
```

### Deteccion de Articulos Antiguos

```bash
export LIMPIAR_ARTICULOS_VIEJOS=true
export DIAS_ANTIGUEDAD_LIMPIAR=1

./tests/run_load_tests.sh baseline
```

Muestra cuantos articulos con mas de N dias existen, sin eliminarlos.

