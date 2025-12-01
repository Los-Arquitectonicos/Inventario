# Pruebas de Escalabilidad y Desempeño - ProvesiWMS

## Objetivo

Evaluar el comportamiento del sistema ProvesiWMS bajo diferentes cargas de trabajo para determinar:
- Capacidad máxima de usuarios concurrentes
- Tiempo de respuesta bajo carga
- Puntos de falla y cuellos de botella
- Estabilidad del sistema en condiciones de estrés

## Estructura de Archivos

### Herramientas de Pruebas de Carga
- `locustfile.py` - Definición de escenarios de carga con Locust
- `config_entornos.py` - Configuración de diferentes entornos de prueba
- `run_load_tests.sh` - Script automatizado para ejecutar pruebas

### Reportes y Análisis
- `reportes/` - Directorio con reportes de pruebas ejecutadas
- `RESUMEN_SIMPLIFICACION_REPORTES.md` - Análisis y conclusiones

## Herramientas Utilizadas

### Locust
Framework Python para pruebas de carga que simula usuarios concurrentes:
- Simula comportamiento real de usuarios
- Escalabilidad gradual de carga
- Métricas en tiempo real
- Reportes detallados

## Escenarios de Prueba

### 1. Baseline (Línea Base)
- **Usuarios**: 10 concurrentes
- **Duración**: 5 minutos
- **Objetivo**: Establecer comportamiento normal del sistema

### 2. Objective (Carga Objetivo)
- **Usuarios**: 50 concurrentes
- **Duración**: 10 minutos
- **Objetivo**: Validar capacidad esperada de producción

### 3. Maximum (Carga Máxima)
- **Usuarios**: 100+ concurrentes
- **Duración**: 15 minutos
- **Objetivo**: Encontrar límites del sistema

## Métricas Evaluadas

### Rendimiento
- **Requests per second (RPS)**: Solicitudes procesadas por segundo
- **Response time**: Tiempo promedio de respuesta
- **Percentiles**: P50, P95, P99 de tiempos de respuesta
- **Throughput**: Volumen de datos procesados

### Confiabilidad
- **Error rate**: Porcentaje de errores
- **Availability**: Disponibilidad del sistema
- **Stability**: Estabilidad bajo carga sostenida

### Recursos
- **CPU usage**: Uso de procesador
- **Memory usage**: Consumo de memoria
- **Database connections**: Conexiones a base de datos

## Configuración de Entornos

### Desarrollo Local
```python
LOCAL_CONFIG = {
    'host': 'http://localhost:8000',
    'users': 10,
    'spawn_rate': 2
}
```

### Staging/Testing
```python
STAGING_CONFIG = {
    'host': 'https://staging.provesi.com',
    'users': 50,
    'spawn_rate': 5
}
```

### Producción
```python
PRODUCTION_CONFIG = {
    'host': 'https://provesi-alb-xxx.us-east-1.elb.amazonaws.com',
    'users': 100,
    'spawn_rate': 10
}
```

## Ejecución de Pruebas

### Prerequisitos
```bash
# Instalar Locust
pip install locust

# Verificar instalación
locust --version
```

### Ejecución Manual
```bash
# Navegar al directorio
cd tests/escalabilidad

# Ejecutar prueba específica
locust -f locustfile.py --host=https://tu-servidor.com

# Ejecutar con configuración automática
./run_load_tests.sh
```

### Ejecución Automatizada
```bash
# Ejecutar suite completa
./run_load_tests.sh

# Ejecutar escenario específico
./run_load_tests.sh baseline
./run_load_tests.sh objective  
./run_load_tests.sh maximum
```

## Análisis de Resultados

### Criterios de Aceptación

#### Baseline (Aceptable)
- Response time < 200ms (P95)
- Error rate < 1%
- RPS > 50

#### Objective (Bueno)
- Response time < 500ms (P95)
- Error rate < 2%
- RPS > 100

#### Maximum (Límite)
- Response time < 1000ms (P95)
- Error rate < 5%
- Sistema no debe caerse

### Indicadores Problemáticos
- Response time > 2000ms = PROBLEMA DE RENDIMIENTO
- Error rate > 10% = FALLA DE ESTABILIDAD
- CPU > 90% sostenido = NECESIDAD DE ESCALAMIENTO
- Memoria > 85% = POSIBLE MEMORY LEAK

## Reportes Generados

### Estructura de Reportes
```
reportes/
├── reporte_baseline_YYYYMMDD_HHMMSS.json
├── reporte_objective_YYYYMMDD_HHMMSS.json
├── reporte_maximum_YYYYMMDD_HHMMSS.json
└── summary_YYYYMMDD.html
```

### Contenido de Reportes
- Estadísticas de requests
- Distribución de tiempos de respuesta
- Gráficos de carga vs rendimiento
- Análisis de errores
- Recomendaciones de optimización

## Optimizaciones Identificadas

### Base de Datos
- Optimización de queries
- Índices apropiados
- Connection pooling
- Query caching

### Aplicación
- Response caching
- Static files serving
- Code profiling
- Memory optimization

### Infraestructura
- Auto-scaling configuration
- Load balancer tuning
- CDN implementation
- Database replication

## Monitoreo Continuo

### Métricas en Producción
- APM (Application Performance Monitoring)
- Real User Monitoring (RUM)
- Infrastructure monitoring
- Database performance

### Alertas Automáticas
- Response time > 1000ms
- Error rate > 5%
- CPU usage > 80%
- Memory usage > 80%

---

**Nota**: Las pruebas de escalabilidad deben ejecutarse regularmente, especialmente antes de releases importantes y después de cambios significativos en la arquitectura del sistema.