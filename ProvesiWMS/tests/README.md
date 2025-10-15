# Pruebas de Carga - Sistema de Inventario WMS

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

### 2. Preparar Datos Base en AWS

Usa Postman para crear los datos iniciales en el servidor AWS:

```bash
cd scripts_llenar_db
python generar_postman_aws.py
```

Importa el archivo `postman_aws_datos_base.json` en Postman y ejecuta la coleccion completa.

**Datos creados:**
- 1 bodega
- 1 ubicacion (capacidad: 20,000 articulos)
- 50 productos

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

Cada prueba genera automaticamente:

1. **HTML** (`reportes/reporte_[nombre].html`)
   - Visualizacion grafica de metricas
   - Tablas de percentiles y errores

2. **CSV** (`reportes/reporte_[nombre]_stats.csv`)
   - Datos crudos para analisis

3. **JSON** (`reporte_locust_[timestamp].json`)
   - Metricas completas con evaluacion automatica

### Metricas Principales

**Request Statistics:**
- **# reqs**: Total de peticiones enviadas
- **# fails**: Peticiones fallidas
- **Avg/Min/Max**: Tiempos de respuesta en milisegundos
- **req/s**: Throughput (peticiones por segundo)

**Response Time Percentiles:**
- **P50**: 50% de requests terminaron en este tiempo o menos
- **P95**: 95% de requests terminaron en este tiempo o menos
- **P99**: 99% de requests terminaron en este tiempo o menos

**Objetivos Evaluados (JSON):**
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


## Generacion de Codigos Unicos

Las pruebas generan codigos de barras EAN-13 unicos automaticamente:

```python
timestamp = int(time.time() * 1000000) % 1000000  # Microsegundos
codigo = timestamp * 1000 + contador
```

**Ventajas:**
- Ejecutar pruebas multiples veces sin conflictos
- Sin necesidad de limpiar base de datos entre ejecuciones
- Garantiza unicidad incluso con alta concurrencia

## Limpieza de Datos (Opcional)

Para eliminar articulos de pruebas anteriores:

```bash
# Eliminar todos los articulos
python manage.py limpiar_articulos --all --yes

# Eliminar articulos con mas de X dias
python manage.py limpiar_articulos --dias 1 --yes

# Ver que se eliminaria sin borrar
python manage.py limpiar_articulos --all --dry-run
```

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
# Sobrescribir URL del servidor
export BASE_URL="http://otro-servidor.com/inventario/"
export TIMEOUT="60"

./tests/run_load_tests.sh objective
```

### Deteccion de Articulos Antiguos

```bash
# Activar deteccion al inicio de pruebas
export LIMPIAR_ARTICULOS_VIEJOS=true
export DIAS_ANTIGUEDAD_LIMPIAR=1

./tests/run_load_tests.sh baseline
```

Esto mostrara cuantos articulos antiguos existen sin eliminarlos.

