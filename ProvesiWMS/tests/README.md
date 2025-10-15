# Pruebas de Carga con Locust

## Resumen

Este directorio contiene las pruebas de carga para validar que el sistema puede escalar de 100 a 2,000 peticiones por minuto, procesando 10,000 registros en menos de 5 minutos mientras mantiene la integridad de datos.

## Estructura de Archivos

- `locustfile.py` - Definiciones de usuarios y tareas de prueba
- `config_entornos.py` - Configuración centralizada (URL, timeouts, umbrales)
- `run_load_tests.sh` - Script de ejecución automatizada
- `.gitignore` - Archivos ignorados por git
- `reportes/` - Directorio para reportes HTML/CSV generados

## Configuración Inicial

### 1. Instalar Locust

```bash
pip install locust
```

### 2. Preparar Datos Base

Antes de ejecutar las pruebas por primera vez, necesitas crear datos iniciales. Ejecuta esto una sola vez:

```bash
python manage.py shell
```

Luego copia y pega este código:

```python
from inventario.models import Bodega, UbicacionBodega, Producto

bodega = Bodega.objects.create(
    nombre="Bodega Test",
    ciudad="Bogota",
    direccion="Calle 1"
)

ubicacion = UbicacionBodega.objects.create(
    bodega=bodega,
    pasillo="A",
    estante="1",
    nivel="1",
    capacidad_total=20000,
    capacidad_disponible=20000
)

for i in range(1, 51):
    Producto.objects.create(
        codigo=f"P{i:03d}",
        nombre=f"Producto {i}",
        precio_unitario=10 * i
    )
```

### 3. Iniciar Servidor Django

```bash
python manage.py runserver
```

## Ejecutar Pruebas

### Opción 1: Interfaz Web (Recomendado para Exploración)

Esta opción te permite ver métricas en tiempo real y ajustar parámetros sobre la marcha:

```bash
./tests/run_load_tests.sh web
```

Abre http://localhost:8089 en tu navegador y configura:
- Number of users: 35
- Spawn rate: 7
- Host: http://127.0.0.1:8000

### Opción 2: Pruebas Automatizadas

El script incluye 5 perfiles predefinidos que puedes ejecutar directamente:

```bash
# Baseline: 100 req/min durante 1 minuto
./tests/run_load_tests.sh baseline

# Carga media: 500 req/min durante 2 minutos
./tests/run_load_tests.sh medium

# Carga alta: 1,000 req/min durante 3 minutos
./tests/run_load_tests.sh high

# Carga máxima: 2,000 req/min durante 3 minutos
./tests/run_load_tests.sh max

# Test objetivo: 10,000 artículos en aproximadamente 5 minutos
./tests/run_load_tests.sh objective

# Ejecutar todos los tests
./tests/run_load_tests.sh all
```

## Interpretar Resultados

### Métricas Principales

Después de cada prueba, verás métricas como estas:

- **Request/s**: Solicitudes procesadas por segundo
- **Response Time (avg)**: Tiempo promedio de respuesta en milisegundos
- **P95/P99**: El 95% y 99% de las peticiones se completan en este tiempo o menos
- **Success Rate**: Porcentaje de peticiones exitosas (buscamos >95%)

### Tipos de Reportes

Cada prueba genera tres tipos de reportes automáticamente:

1. **HTML** (`reportes/reporte_[nombre].html`)
   - Reportes interactivos con gráficas
   - Perfecto para presentaciones o análisis visual

2. **CSV** (`reportes/reporte_[nombre]_stats.csv`)
   - Datos crudos para análisis detallado
   - Útil para importar a Excel o herramientas de análisis

3. **JSON** (`reporte_locust_[timestamp].json`)
   - Métricas completas con evaluación automática
   - Incluye validación de objetivos cumplidos

### Evaluación Automática

El sistema evalúa automáticamente si se cumplen los objetivos. Busca esta sección en el JSON:

```json
{
  "objetivos_cumplidos": {
    "tiempo_ejecucion": true,
    "tasa_exito": true,
    "throughput_promedio": true
  }
}
```

## Configuración

### Cambiar Puerto o Servidor

Si necesitas apuntar a un servidor diferente o puerto, edita `config_entornos.py`:

```python
# Desarrollo local (puerto por defecto)
BASE_URL = "http://127.0.0.1:8000"

# Desarrollo local (puerto personalizado)
BASE_URL = "http://127.0.0.1:8080"

# Servidor remoto
BASE_URL = "http://your-server.com:80"

# AWS Load Balancer
BASE_URL = "http://your-alb.amazonaws.com:80"
```

### Ajustar Umbrales de Éxito

También en `config_entornos.py`:

```python
UMBRAL_EXITO_PCT = 95  # Porcentaje mínimo de éxito
TIMEOUT = 30           # Timeout en segundos para cada request
```

## Cómo Funciona

### Tipos de Usuarios Simulados

Locust simula dos tipos de usuarios para hacer las pruebas más realistas:

**UsuarioArticulos (80% del tráfico)**
- Comportamiento realista de un usuario normal
- 50% del tiempo: crea nuevos artículos
- 30% del tiempo: lista artículos existentes
- 20% del tiempo: consulta detalles de artículos

**UsuarioIntensivo (20% del tráfico)**
- Generación pura de carga
- 100% del tiempo: crea artículos continuamente
- Simula procesos batch o integraciones

## Notas Importantes

### Base de Datos

- **Desarrollo**: Actualmente usa SQLite, que tiene limitaciones de concurrencia
- **Producción**: Requiere PostgreSQL o MySQL para soportar alta concurrencia
- Para cambiar a PostgreSQL, solo actualiza `settings.py` - las pruebas no necesitan cambios

### Thread-Safety

El método `ocupar_espacio()` en el código utiliza:
- `select_for_update()`: Bloquea filas durante la transacción
- `F()` expressions: Actualizaciones atómicas en la base de datos
- `transaction.atomic()`: Garantiza transacciones ACID

Esto asegura que no haya condiciones de carrera incluso con miles de peticiones concurrentes.

## Solución de Problemas

### Error: "Connection refused"

**Problema**: No puede conectarse al servidor Django.

**Solución**:
1. Verifica que Django esté corriendo: `python manage.py runserver`
2. Confirma que el puerto en `config_entornos.py` coincida con el servidor
3. Verifica que no haya firewall bloqueando el puerto

### Error: "ImportError: No module named locust"

**Problema**: Locust no está instalado.

**Solución**:
```bash
pip install locust
```

### Tasa de Éxito Baja (<95%)

**Problema**: Muchas peticiones fallan o dan error.

**Posibles causas y soluciones**:
1. **Sobrecarga del servidor**
   - Reduce el número de usuarios o spawn rate
   - Aumenta la capacidad del servidor

2. **Base de datos saturada**
   - Considera usar PostgreSQL en lugar de SQLite
   - Revisa índices en las tablas

3. **Errores en la aplicación**
   - Revisa los logs de Django para ver errores específicos
   - Verifica que haya suficiente capacidad en las ubicaciones

### Timeouts Frecuentes

**Problema**: Muchas peticiones exceden el tiempo límite.

**Soluciones**:
1. Aumenta `TIMEOUT` en `config_entornos.py`
2. Reduce la carga concurrente
3. Optimiza las consultas de base de datos (usa `select_related`, `prefetch_related`)
4. Considera agregar cache

## Próximos Pasos

Una vez que las pruebas locales funcionen correctamente:

1. Migra a PostgreSQL para producción
2. Configura el load balancer y actualiza `BASE_URL`
3. Ejecuta las pruebas contra el ambiente de staging
4. Valida que todos los objetivos se cumplan
5. Documenta los resultados para el equipo

