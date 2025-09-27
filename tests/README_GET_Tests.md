# JMeter - Pruebas GET de Inventario de Productos

Este archivo JMX está diseñado específicamente para realizar pruebas de carga únicamente en las operaciones GET del sistema de inventario de productos.

## 🎯 Enfoque de las Pruebas

### Operaciones Incluidas (Solo GET)
- ✅ **GET /api/productos/** - Lista completa de productos
- ✅ **GET /api/productos/{id}/** - Detalles de producto específico
- ✅ **GET /api/bodegas/** - Lista de bodegas/almacenes
- ✅ **GET /api/bodegas/{id}/inventario/** - **Prueba principal** - Inventario por bodega
- ✅ **GET /api/productos/{id}/articulos/** - Artículos de un producto
- ✅ **GET /api/articulos/{id}/movimientos/** - Historial de movimientos

### Operaciones Excluidas
- ❌ POST (Crear productos, artículos)
- ❌ PUT (Actualizar estados, datos)
- ❌ DELETE (Eliminar registros)

## 🔧 Configuración Predeterminada

### Parámetros del Test
- **Hilos (Usuarios)**: 20 usuarios concurrentes
- **Tiempo de Rampeo**: 30 segundos
- **Bucles**: 5 iteraciones por hilo
- **Servidor**: http://127.0.0.1:8000
- **Intervalo**: 1 segundo entre peticiones

### Variables Configurables
```bash
# Ejecutar con parámetros personalizados
jmeter -n -t tests/inventario_get_only_test.jmx \
  -Jserver.host=127.0.0.1 \
  -Jserver.port=8000 \
  -Jthreads=30 \
  -Jramp.time=45 \
  -Jloops=10
```

## 📊 Pruebas de Rendimiento Específicas

### 1. Lista de Productos
- **Endpoint**: `/api/productos/`
- **Esperado**: < 200ms
- **Validación**: Estructura JSON con array "productos"

### 2. Producto Individual
- **Endpoint**: `/api/productos/{1-10}/`
- **Esperado**: < 100ms
- **Validación**: JSON con campo "id"

### 3. Lista de Bodegas
- **Endpoint**: `/api/bodegas/`
- **Esperado**: < 150ms
- **Validación**: Estructura JSON con array "bodegas"

### 4. **Inventario de Bodega (Prueba Principal)**
- **Endpoint**: `/api/bodegas/{1-2}/inventario/`
- **Esperado**: < 800ms (consulta compleja)
- **Validación**: JSON con "inventario" y "bodega"
- **Importancia**: Esta es la consulta más crítica del sistema

### 5. Artículos por Producto
- **Endpoint**: `/api/productos/{1-6}/articulos/`
- **Esperado**: < 300ms
- **Validación**: Array "articulos"

### 6. Movimientos de Artículo
- **Endpoint**: `/api/articulos/{1-24}/movimientos/`
- **Esperado**: < 400ms
- **Validación**: Array "movimientos"

## 🚀 Cómo Ejecutar

### Preparación
1. **Crear datos de prueba**:
   ```bash
   cd /Users/pedropablosanintrujillo/GitHub/Inventario
   python tests/create_test_data.py
   ```

2. **Iniciar servidor Django**:
   ```bash
   python manage.py runserver 8000
   ```

### Ejecución en GUI (Recomendado para desarrollo)
```bash
jmeter -t tests/inventario_get_only_test.jmx
```

### Ejecución en línea de comandos (Para CI/CD)
```bash
jmeter -n -t tests/inventario_get_only_test.jmx \
  -l resultados_get.jtl \
  -e -o reporte_get/
```

### Prueba de carga alta
```bash
jmeter -n -t tests/inventario_get_only_test.jmx \
  -Jthreads=50 \
  -Jramp.time=60 \
  -Jloops=20 \
  -l carga_alta_get.jtl \
  -e -o reporte_carga_alta/
```

## 📈 Métricas Esperadas

### Rendimiento Objetivo
- **Tiempo de respuesta promedio**: < 400ms
- **95º percentil**: < 1000ms
- **Throughput mínimo**: 50 req/seg
- **Tasa de error**: 0%

### Puntos de referencia por endpoint
| Endpoint | Resp. Promedio | 95º Percentil | Throughput |
|----------|---------------|---------------|------------|
| Lista productos | < 200ms | < 500ms | 100+ req/s |
| Producto individual | < 100ms | < 300ms | 150+ req/s |
| Lista bodegas | < 150ms | < 400ms | 120+ req/s |
| **Inventario bodega** | < 800ms | < 1500ms | 25+ req/s |
| Artículos producto | < 300ms | < 600ms | 80+ req/s |
| Movimientos artículo | < 400ms | < 800ms | 60+ req/s |

## 🔍 Validaciones Incluidas

### Código de Respuesta HTTP
- Todas las peticiones deben retornar **200 OK**
- Mensajes de error descriptivos en español

### Estructura JSON
- **productos**: Debe contener array "productos"
- **producto individual**: Debe contener campo "id"
- **bodegas**: Debe contener array "bodegas"
- **inventario**: Debe contener "inventario" y "bodega"
- **articulos**: Debe contener array "articulos"
- **movimientos**: Debe contener array "movimientos"

### Timeouts Configurados
- **Conexión**: 5 segundos
- **Respuesta**: 10-15 segundos (15s para inventario)

## 📊 Reportes Generados

### Listeners Incluidos
1. **Ver Resultados Detallados** - Debug individual de peticiones
2. **Resumen de Resultados** - Métricas de rendimiento general
3. **Gráfico de Resultados** - Tendencias de tiempo de respuesta
4. **Reporte Agregado** - Estadísticas completas por endpoint

### Archivos de Salida
- `resultados_get.jtl` - Datos en bruto
- `reporte_get/index.html` - Dashboard HTML interactivo
- Gráficos de rendimiento por endpoint

## 🎯 Casos de Uso Específicos

### 1. Validación de Rendimiento
```bash
# Probar con carga normal
jmeter -n -t tests/inventario_get_only_test.jmx \
  -Jthreads=20 -Jloops=5 -l normal.jtl
```

### 2. Prueba de Estrés
```bash
# Incrementar carga gradualmente
jmeter -n -t tests/inventario_get_only_test.jmx \
  -Jthreads=100 -Jramp.time=120 -Jloops=10 -l estres.jtl
```

### 3. Prueba de Resistencia
```bash
# Carga sostenida por tiempo extendido
jmeter -n -t tests/inventario_get_only_test.jmx \
  -Jthreads=25 -Jloops=50 -l resistencia.jtl
```

## ⚠️ Consideraciones Importantes

### Limitaciones
- **Solo pruebas de lectura**: No modifica datos
- **Rango de IDs fijo**: Productos 1-10, Bodegas 1-2, Artículos 1-24
- **Sin autenticación**: Asume endpoints públicos

### Recomendaciones
- Ejecutar con datos de prueba poblados
- Monitorear uso de memoria del servidor Django
- Verificar conexiones de base de datos disponibles
- Revisar logs de Django durante las pruebas

### Optimización de Base de Datos
Para mejores resultados, considerar:
- Índices en campos ID frecuentemente consultados
- Optimización de consultas de inventario
- Pool de conexiones adecuado
- Cache de consultas frecuentes

Este archivo JMX está optimizado específicamente para evaluar el rendimiento de las operaciones de consulta del sistema de inventario, enfocándose en la experiencia de usuario para visualización de datos.