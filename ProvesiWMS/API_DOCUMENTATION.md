# API Documentation - ProvesiWMS

## APIs para Listar Todos los Modelos

Se han implementado APIs REST completas para todos los modelos del sistema, con soporte para paginación, filtros y respuestas JSON estructuradas.

### 🔗 Endpoints Disponibles

| Endpoint | Descripción | Filtros Disponibles |
|----------|-------------|-------------------|
| `GET /inventario/api/productos/` | Lista todos los productos | marca, precio_min, precio_max, sin_stock |
| `GET /inventario/api/bodegas/` | Lista todas las bodegas | ciudad |
| `GET /inventario/api/ubicaciones/` | Lista todas las ubicaciones | bodega_id, pasillo, disponible |
| `GET /inventario/api/clientes/` | Lista todos los clientes | ciudad, email |
| `GET /inventario/api/usuarios/` | Lista todos los usuarios | rol |
| `GET /inventario/api/pedidos/` | Lista todos los pedidos | estado, cliente_id, fecha_inicio, fecha_fin |
| `GET /inventario/api/cotizaciones/` | Lista todas las cotizaciones | cliente_id, estado, vigente |
| `GET /inventario/api/facturas/` | Lista todas las facturas | metodo_pago, fecha_inicio, fecha_fin |
| `GET /inventario/api/articulos/` | Lista todos los artículos | producto_id, ubicacion_id, sin_salida, bodega_id, codigo_barras, pasillo |

### Parámetros de Paginación

Todos los endpoints soportan los siguientes parámetros:
- `limit`: Número máximo de resultados (default: 100)
- `offset`: Número de registros a omitir (default: 0)

### Ejemplos de Uso

#### 1. Listar Productos con Filtros
```bash
# Productos de marca Apple con límite de 5
curl "http://127.0.0.1:8001/inventario/api/productos/?marca=Apple&limit=5"

# Productos sin stock
curl "http://127.0.0.1:8001/inventario/api/productos/?sin_stock=true"

# Productos en rango de precio
curl "http://127.0.0.1:8001/inventario/api/productos/?precio_min=100&precio_max=500"
```

#### 2. Listar Bodegas
```bash
# Todas las bodegas con paginación
curl "http://127.0.0.1:8001/inventario/api/bodegas/?limit=10&offset=0"

# Bodegas en Bogotá
curl "http://127.0.0.1:8001/inventario/api/bodegas/?ciudad=Bogotá"
```

#### 3. Listar Ubicaciones con Disponibilidad
```bash
# Ubicaciones disponibles (con capacidad > 0)
curl "http://127.0.0.1:8001/inventario/api/ubicaciones/?disponible=true"

# Ubicaciones de una bodega específica
curl "http://127.0.0.1:8001/inventario/api/ubicaciones/?bodega_id=1"
```

#### 4. Listar Pedidos por Estado y Fecha
```bash
# Pedidos pendientes
curl "http://127.0.0.1:8001/inventario/api/pedidos/?estado=pendiente"

# Pedidos entre fechas específicas
curl "http://127.0.0.1:8001/inventario/api/pedidos/?fecha_inicio=2025-01-01&fecha_fin=2025-12-31"
```

### Estructura de Respuesta

Todas las APIs retornan una respuesta JSON con la siguiente estructura:

```json
{
    "success": true,
    "count": 2,
    "total": 51,
    "offset": 0,
    "limit": 2,
    "has_next": true,
    "has_previous": false,
    "data_field": [
        // Array de objetos específicos del modelo
    ]
}
```

### Características Implementadas

**Paginación Completa**: Todos los endpoints soportan limit/offset  
**Filtros Específicos**: Cada modelo tiene filtros relevantes  
**Relaciones Optimizadas**: Uso de select_related para mejor rendimiento  
**Datos Calculados**: Incluye campos computados como márgenes, totales, etc.  
**Manejo de Errores**: Respuestas estructuradas para errores 400/500  
**Validación de Parámetros**: Validación de tipos y valores  
**Información de Estado**: Campos booleanos como hay_stock, esta_vigente, etc.  

### Información Adicional por Modelo

#### Productos (`/api/productos/`)
- Margen de ganancia calculado automáticamente
- Estado de stock (hay_stock)
- Filtros por precio, marca y disponibilidad

#### Bodegas (`/api/bodegas/`)
- Capacidad total calculada de ubicaciones
- Conteo de ubicaciones por bodega

#### Ubicaciones (`/api/ubicaciones/`)
- Porcentaje de ocupación calculado
- Estado de capacidad (esta_llena)
- Conteo de artículos por ubicación

#### Clientes (`/api/clientes/`)
- Estadísticas de pedidos totales y pendientes

#### Pedidos (`/api/pedidos/`)
- Total calculado dinámicamente
- Información del cliente incluida
- Estado de cancelación disponible

#### Artículos (`/api/articulos/`)
- Información completa del producto
- Detalles de ubicación y bodega
- Estado de salida

### 🚀 Rendimiento

- **Consultas Optimizadas**: Uso de select_related para evitar N+1 queries
- **Paginación Eficiente**: Control de carga de datos
- **Filtros a Nivel DB**: Filtrado en base de datos, no en Python
- **Campos Calculados**: Cálculos eficientes con agregaciones Django

### Pruebas Realizadas

Todas las APIs han sido probadas exitosamente con:
- Respuesta correcta de estructura JSON
- Paginación funcional (has_next/has_previous)
- Filtros operativos
- Manejo de datos vacíos
- Relaciones correctamente cargadas
- Campos calculados funcionando

**Total de endpoints implementados: 8 APIs completas**