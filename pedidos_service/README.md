# Pedidos Service - Microservicio de Gestión de Pedidos

Microservicio FastAPI para gestión de pedidos del sistema ProvesiWMS.

## 📋 Descripción

Este microservicio maneja la creación, consulta, actualización y cancelación de pedidos. Se comunica con el servicio Django InventarioWMS para validar productos y obtener información de clientes, pero mantiene su propia base de datos MongoDB para almacenar pedidos.

## 🏗️ Arquitectura

- **Framework**: FastAPI (Python 3.10+)
- **Base de Datos**: MongoDB (async con Motor)
- **Puerto**: 8002
- **Comunicación**: HTTP REST con Django InventarioWMS

### Flujo de Datos

```
Cliente → Kong Gateway → Pedidos Service → Django InventarioWMS (validación)
                              ↓
                          MongoDB (persistencia)
```

## 🚀 Instalación

### Requisitos

- Python 3.10+
- MongoDB 5.0+
- Acceso al servicio Django InventarioWMS

### Setup Local

1. **Clonar y navegar al directorio**:
```bash
cd pedidos_service
```

2. **Crear entorno virtual**:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Iniciar el servicio**:
```bash
# Opción 1: Usando script
bash start_service.sh

# Opción 2: Usando Python directamente
python3 -m uvicorn pedidos_service.main:app --host 0.0.0.0 --port 8002
```

## 📡 API Endpoints

### Health Check

**GET** `/health`

Verifica el estado del servicio y sus dependencias.

**Response**:
```json
{
  "status": "healthy",
  "service": "pedidos-service",
  "dependencies": {
    "mongodb": "ok",
    "django_inventario": "ok"
  }
}
```

### Crear Pedido

**POST** `/pedidos`

Crea un nuevo pedido validando productos y stock en Django.

**Request Body**:
```json
{
  "cliente_id": 1,
  "productos": [
    {
      "producto_id": 5,
      "cantidad": 3
    }
  ],
  "notas": "Entregar antes de las 5pm"
}
```

**Response** (201):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "numero_pedido": "PED-000001",
  "estado": "pendiente",
  "fecha_creacion": "2024-01-15T10:30:00",
  "cliente_id": 1,
  "cliente_info": {
    "nombre": "Juan Pérez",
    "email": "juan@example.com"
  },
  "productos": [
    {
      "producto_id": 5,
      "nombre": "Camiseta Azul",
      "cantidad": 3,
      "precio_unitario": 25.00,
      "subtotal": 75.00
    }
  ],
  "total": 75.00,
  "timestamps": {
    "pendiente": "2024-01-15T10:30:00"
  },
  "notas": "Entregar antes de las 5pm"
}
```

### Listar Pedidos

**GET** `/pedidos`

Lista pedidos con filtros opcionales y paginación.

**Query Parameters**:
- `estado` (optional): Filtrar por estado (`pendiente`, `preparando`, etc.)
- `cliente_id` (optional): Filtrar por cliente
- `skip` (default: 0): Offset para paginación
- `limit` (default: 100, max: 1000): Número de resultados

**Response** (200):
```json
{
  "total": 50,
  "pedidos": [
    {
      "id": "507f1f77bcf86cd799439011",
      "numero_pedido": "PED-000001",
      "estado": "pendiente",
      "fecha_creacion": "2024-01-15T10:30:00",
      "cliente_id": 1,
      "total": 75.00,
      "productos": [...]
    }
  ]
}
```

### Obtener Pedido

**GET** `/pedidos/{numero_pedido}`

Obtiene un pedido específico por número.

**Response** (200): Mismo formato que crear pedido.

### Actualizar Estado

**PATCH** `/pedidos/{numero_pedido}/estado`

Actualiza el estado de un pedido según máquina de estados.

**Request Body**:
```json
{
  "nuevo_estado": "preparando"
}
```

**Response** (200): Pedido actualizado.

### Cancelar Pedido

**POST** `/pedidos/{numero_pedido}/cancelar`

Cancela un pedido (solo si está en `pendiente` o `preparando`).

**Response** (200): Pedido cancelado.

## 🔄 Máquina de Estados

Estados posibles y transiciones válidas:

```
PENDIENTE → PREPARANDO → LISTO → ENVIADO → ENTREGADO
    ↓           ↓          ↓
CANCELADO   CANCELADO  CANCELADO
```

**Estados**:
- `pendiente`: Pedido creado, esperando procesamiento
- `preparando`: En proceso de alistamiento
- `listo`: Listo para envío
- `enviado`: Enviado al cliente
- `entregado`: Entregado y completado (estado final)
- `cancelado`: Cancelado (estado final)

**Reglas**:
- Solo se puede cancelar desde `pendiente` o `preparando`
- Estados finales (`entregado`, `cancelado`) no tienen transiciones

## 🗄️ Modelo de Datos (MongoDB)

### Colección: `orders`

```javascript
{
  "_id": ObjectId,
  "numero_pedido": "PED-000001",  // Único, autogenerado
  "estado": "pendiente",
  "fecha_creacion": ISODate,
  "fecha_completado": ISODate | null,
  "cliente_id": 1,
  "cliente_info": {
    "nombre": "Juan Pérez",
    "email": "juan@example.com"
  },
  "productos": [
    {
      "producto_id": 5,
      "nombre": "Camiseta Azul",
      "cantidad": 3,
      "precio_unitario": 25.00
    }
  ],
  "total": 75.00,
  "timestamps": {
    "pendiente": ISODate,
    "preparando": ISODate | null,
    "listo": ISODate | null,
    "enviado": ISODate | null,
    "entregado": ISODate | null,
    "cancelado": ISODate | null
  },
  "notas": "Entregar antes de las 5pm"
}
```

### Índices

- `numero_pedido` (unique)
- `cliente_id`
- `estado`
- `fecha_creacion` (descending)

## 🔧 Configuración

Variables de entorno (`.env`):

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017/orders_db

# Django InventarioWMS
DJANGO_API_URL=http://localhost:8080

# Configuración del servicio
SERVICE_PORT=8002
LOG_LEVEL=INFO
```

## 🧪 Testing

### Probar Health Check

```bash
curl http://localhost:8002/health
```

### Crear Pedido de Prueba

```bash
curl -X POST http://localhost:8002/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "productos": [
      {"producto_id": 5, "cantidad": 2}
    ],
    "notas": "Prueba"
  }'
```

### Listar Pedidos

```bash
curl http://localhost:8002/pedidos?estado=pendiente&limit=10
```

## 📚 Documentación Interactiva

Una vez iniciado el servicio, accede a:

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## 🐳 Despliegue en AWS (con Terraform)

El servicio se despliega automáticamente en AWS EC2 mediante Terraform. Ver `terraform/main.tf` para configuración completa.

**Arquitectura en AWS**:
- 1 EC2 t3.small para aplicación (Ubuntu 24.04)
- 1 EC2 t3.small para MongoDB
- Security Groups para puertos 8002 (app) y 27017 (mongo)
- Integración con Kong Gateway existente

## 🔒 Seguridad

- **Autenticación**: Gestionada por Kong Gateway (no JWT en este servicio)
- **Validación**: Pydantic para todos los inputs
- **MongoDB**: Indices únicos para evitar duplicados
- **CORS**: Configurado para todos los orígenes (ajustar en producción)

## 📝 Scripts

- `start_service.sh`: Inicia el servicio (crea venv, instala deps, ejecuta)
- `restart_service.sh`: Reinicia el servicio (mata procesos y reinicia)

Hacer ejecutables:
```bash
chmod +x start_service.sh restart_service.sh
```

## 🔍 Logs

Los logs se muestran en stdout con formato:

```
2024-01-15 10:30:00 - pedidos_service.main - INFO - 🚀 Iniciando Pedidos Service...
2024-01-15 10:30:01 - pedidos_service.database - INFO - ✅ Conectado a MongoDB
2024-01-15 10:30:02 - pedidos_service.services.order_service - INFO - Pedido PED-000001 creado
```

## 🛠️ Desarrollo

### Estructura del Proyecto

```
pedidos_service/
├── __init__.py
├── main.py                 # Aplicación FastAPI
├── config.py               # Configuración (Pydantic Settings)
├── database.py             # Gestor de MongoDB
├── models/                 # Modelos MongoDB
│   ├── __init__.py
│   ├── order.py            # Order, OrderProduct
│   └── enums.py            # OrderStatus, transiciones
├── schemas/                # Schemas Pydantic
│   ├── __init__.py
│   └── order.py            # Request/Response schemas
├── routes/                 # Endpoints FastAPI
│   ├── __init__.py
│   ├── health.py           # Health check
│   └── orders.py           # CRUD pedidos
├── services/               # Lógica de negocio
│   ├── __init__.py
│   ├── inventory_client.py # Cliente HTTP Django
│   └── order_service.py    # Servicio de pedidos
├── requirements.txt
├── .env.example
├── start_service.sh
├── restart_service.sh
└── README.md
```

### Agregar Nueva Funcionalidad

1. Definir schema en `schemas/`
2. Implementar lógica en `services/`
3. Crear endpoint en `routes/`
4. Registrar router en `main.py`

## 🤝 Integración con Sistema Existente

### Comunicación con Django

El servicio consulta Django para:
- **Validar productos** (`GET /api/productos/{id}/`)
- **Obtener info de clientes** (`GET /api/clientes/{id}/`)

**Importante**: Solo lectura, no modifica datos en Django.

### Integración con Kong

Kong debe configurarse con la ruta:

```yaml
routes:
  - name: pedidos-service
    paths:
      - /pedidos
    methods:
      - GET
      - POST
      - PATCH
    service:
      url: http://pedidos-service:8002
```

## ⚠️ Limitaciones Conocidas

- No reduce stock en Django automáticamente
- Sin autenticación propia (depende de Kong)
- CORS abierto (ajustar en producción)
- Sin rate limiting (gestionar en Kong)

## 📞 Soporte

Para problemas o preguntas, revisar:
1. Logs del servicio
2. Health check (`/health`)
3. Documentación interactiva (`/docs`)

## 📄 Licencia

Proyecto académico - Los Arquitectonicos
