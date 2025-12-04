# 🚀 Lambda Pedidos - Gestión Serverless de Pedidos

Sistema de gestión de pedidos implementado con **AWS Lambda** y **MongoDB**, utilizando arquitectura serverless para escalabilidad y eficiencia de costos.

## 📋 Arquitectura

```
┌─────────────────┐
│   API Gateway   │ ← Endpoints REST públicos
└────────┬────────┘
         │
    ┌────┴────────────────────────┐
    │                             │
┌───▼────────┐  ┌────────────┐  ┌▼──────────┐
│   Lambda   │  │  Lambda    │  │  Lambda   │
│   Crear    │  │ Consultar  │  │  Seguir   │
│  Pedido    │  │  Pedido    │  │  Pedido   │
└─────┬──────┘  └──────┬─────┘  └─────┬─────┘
      │                │               │
      └────────────────┴───────────────┘
                       │
              ┌────────▼────────┐
              │  Lambda Layer   │ ← Código compartido
              │  - models       │   (pymongo, requests)
              │  - db_client    │
              │  - provesi_api  │
              └────────┬────────┘
                       │
      ┌────────────────┴────────────────┐
      │                                  │
┌─────▼─────────┐              ┌────────▼────────┐
│   MongoDB     │              │   ProvesiWMS    │
│   EC2         │              │   Django API    │
│   (pedidos)   │              │ (validaciones)  │
└───────────────┘              └─────────────────┘
```

### Componentes

- **API Gateway**: REST API regional con CORS
- **Lambda Functions**: 3 funciones serverless (Python 3.11)
- **Lambda Layer**: Código compartido entre funciones
- **MongoDB EC2**: Base de datos en instancia t3.small
- **ProvesiWMS**: Validación de productos y clientes
- **Terraform**: Infraestructura como código

## 🎯 Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/pedidos` | Crear nuevo pedido |
| `GET` | `/pedidos` | Listar pedidos con filtros |
| `GET` | `/pedidos/{numero_pedido}` | Obtener pedido específico |
| `PUT` | `/pedidos/{numero_pedido}/seguimiento` | Actualizar estado del pedido |

## 📦 Estructura del Proyecto

```
lambda_pedidos/
├── functions/              # Funciones Lambda
│   ├── crear_pedido.py     # POST /pedidos
│   ├── consultar_pedido.py # GET /pedidos
│   └── seguir_pedido.py    # PUT /pedidos/{id}/seguimiento
├── layer/                  # Lambda Layer
│   ├── python/
│   │   ├── models.py       # Modelos (Order, OrderProduct)
│   │   ├── db_client.py    # Cliente MongoDB
│   │   ├── provesi_client.py # Cliente ProvesiWMS
│   │   └── response_builder.py # Respuestas API Gateway
│   └── requirements.txt    # pymongo, requests
├── terraform/              # Infraestructura
│   ├── providers.tf        # Configuración AWS
│   ├── variables.tf        # Variables de entrada
│   ├── mongodb.tf          # Instancia EC2 MongoDB
│   ├── lambda.tf           # Funciones Lambda + Layer
│   ├── api_gateway.tf      # REST API
│   └── outputs.tf          # URLs y recursos
├── scripts/                # Scripts de despliegue
│   ├── package.sh          # Empaquetar funciones
│   ├── deploy.sh           # Desplegar infraestructura
│   └── test_endpoints.sh   # Probar endpoints
└── README.md
```

## 🛠️ Requisitos Previos

### Software

- **Python 3.11+**
- **Terraform 1.0+**
- **AWS CLI 2.x**
- **jq** (para scripts de prueba)

### AWS

- Cuenta AWS configurada (`aws configure`)
- VPC con subnets públicas/privadas
- EC2 Key Pair para SSH
- Permisos IAM para crear:
  - Lambda Functions
  - API Gateway
  - EC2 Instances
  - IAM Roles
  - CloudWatch Logs

## 🚀 Despliegue

### 0. Clonar Repositorio (en CloudShell)

```bash
git clone -b servicediscovery https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario/lambda_pedidos
```

### 1. Configurar Variables

Crea `terraform/terraform.tfvars`:

```hcl
aws_region          = "us-east-1"
provesi_api_url     = "http://tu-ip-provesi:8000"
key_name            = "mi-keypair"
vpc_id              = "vpc-xxxxxxxxx"
subnet_id           = "subnet-xxxxxxxxx"

# Opcional
mongodb_instance_type = "t3.small"
mongodb_volume_size   = 20
```

### 2. Empaquetar Funciones

```bash
cd lambda_pedidos
./scripts/package.sh
```

Esto genera:
- `layer.zip` (código compartido + dependencias)
- `functions/crear_pedido.zip`
- `functions/consultar_pedido.zip`
- `functions/seguir_pedido.zip`

### 3. Desplegar Infraestructura

```bash
./scripts/deploy.sh
```

El script:
1. ✅ Verifica requisitos (Terraform, AWS CLI, credenciales)
2. 📦 Valida archivos empaquetados
3. 🔧 Inicializa Terraform
4. 📋 Genera plan de ejecución
5. ⚠️ Solicita confirmación
6. 🚀 Despliega infraestructura
7. 📊 Muestra URLs y outputs

**Tiempo estimado**: 5-7 minutos

### 4. Probar Endpoints

Espera ~3 minutos para que MongoDB se inicialice, luego:

```bash
./scripts/test_endpoints.sh
```

El script ejecuta:
1. Crear pedido (`POST /pedidos`)
2. Consultar pedido (`GET /pedidos/{numero}`)
3. Listar pedidos (`GET /pedidos?filters`)
4. Actualizar estado a `confirmado`
5. Actualizar estado a `en_preparacion`
6. Intentar transición inválida (debe fallar)

## 📚 Uso del API

### 1. Crear Pedido

```bash
curl -X POST https://api-gateway-url/prod/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "productos": [
      {"producto_id": 1, "cantidad": 10},
      {"producto_id": 2, "cantidad": 5}
    ]
  }'
```

**Respuesta** (201 Created):

```json
{
  "numero_pedido": "PED-000001",
  "cliente_id": 1,
  "productos": [
    {
      "producto_id": 1,
      "cantidad": 10,
      "nombre_producto": "Producto A",
      "precio_unitario": 100.0
    }
  ],
  "total": 1000.0,
  "estado": "pendiente",
  "fecha_creacion": "2024-01-15T10:30:00",
  "historial_estados": [
    {
      "estado": "pendiente",
      "timestamp": "2024-01-15T10:30:00"
    }
  ]
}
```

### 2. Consultar Pedido

```bash
curl https://api-gateway-url/prod/pedidos/PED-000001
```

### 3. Listar Pedidos

```bash
# Todos los pedidos del cliente 1
curl "https://api-gateway-url/prod/pedidos?cliente_id=1"

# Filtrar por estado con paginación
curl "https://api-gateway-url/prod/pedidos?estado=confirmado&skip=0&limit=10"
```

### 4. Actualizar Estado

```bash
curl -X PUT https://api-gateway-url/prod/pedidos/PED-000001/seguimiento \
  -H "Content-Type: application/json" \
  -d '{"nuevo_estado": "confirmado"}'
```

## 🔄 Máquina de Estados

El sistema implementa transiciones válidas entre estados:

```
pendiente → confirmado → en_preparacion → en_camino → entregado
    ↓           ↓              ↓              ↓
cancelado   cancelado      cancelado      cancelado
```

**Estados válidos**:
- `pendiente`: Pedido creado, esperando confirmación
- `confirmado`: Pedido confirmado por el cliente
- `en_preparacion`: Pedido siendo preparado en bodega
- `en_camino`: Pedido en tránsito
- `entregado`: Pedido entregado al cliente
- `cancelado`: Pedido cancelado (desde cualquier estado)

**Transiciones permitidas**:

| Estado Actual | Estados Permitidos |
|---------------|-------------------|
| `pendiente` | `confirmado`, `cancelado` |
| `confirmado` | `en_preparacion`, `cancelado` |
| `en_preparacion` | `en_camino`, `cancelado` |
| `en_camino` | `entregado`, `cancelado` |
| `entregado` | *(ninguno - estado final)* |
| `cancelado` | *(ninguno - estado final)* |

## 🗄️ Modelo de Datos

### Colección: `orders`

```json
{
  "_id": ObjectId("..."),
  "numero_pedido": "PED-000001",
  "cliente_id": 1,
  "productos": [
    {
      "producto_id": 1,
      "cantidad": 10,
      "nombre_producto": "Producto A",
      "precio_unitario": 100.0
    }
  ],
  "total": 1000.0,
  "estado": "confirmado",
  "fecha_creacion": ISODate("2024-01-15T10:30:00Z"),
  "fecha_actualizacion": ISODate("2024-01-15T11:00:00Z"),
  "historial_estados": [
    {
      "estado": "pendiente",
      "timestamp": ISODate("2024-01-15T10:30:00Z")
    },
    {
      "estado": "confirmado",
      "timestamp": ISODate("2024-01-15T11:00:00Z")
    }
  ]
}
```

### Índices MongoDB

- `numero_pedido` (unique): Búsqueda rápida por número
- `cliente_id`: Filtrado por cliente
- `estado`: Filtrado por estado
- `fecha_creacion` (desc): Ordenamiento cronológico

## 🔍 Monitoreo y Logs

### CloudWatch Logs

```bash
# Ver logs de crear_pedido
aws logs tail /aws/lambda/pedidos-crear --follow

# Ver logs de API Gateway
aws logs tail /aws/apigateway/pedidos-api --follow

# Buscar errores
aws logs filter-pattern /aws/lambda/pedidos-crear --filter-pattern "ERROR"
```

### Métricas Lambda

```bash
# Invocaciones en las últimas 24h
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=pedidos-crear \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### X-Ray Tracing

El API Gateway tiene X-Ray habilitado. Ver trazas en:
- AWS Console → X-Ray → Traces
- Buscar por `pedidos-api`

## 🔐 Seguridad

### IAM Roles

- **Lambda Execution Role**: 
  - CloudWatch Logs (escritura)
  - VPC Access (ENI management)
  
### Network

- Lambda en VPC privada
- MongoDB en subnet privada (puerto 27017 solo desde Lambda SG)
- API Gateway público (REGIONAL)

### Secrets

- ⚠️ `MONGODB_URI` y `PROVESI_API_URL` en variables de entorno
- 🔐 **Mejora recomendada**: Usar AWS Secrets Manager

## 🧹 Limpieza

Para destruir toda la infraestructura:

```bash
cd terraform
terraform destroy
```

Esto elimina:
- Funciones Lambda (3)
- Lambda Layer
- API Gateway
- Instancia EC2 MongoDB
- Security Groups
- IAM Roles
- CloudWatch Logs

**Costo estimado mensual**: ~$15-20 USD (t3.small + 1M requests/mes)

## 🛠️ Desarrollo Local

### Instalar Dependencias

```bash
cd layer
pip install -r requirements.txt
```

### Ejecutar Tests Unitarios

```bash
# TODO: Implementar tests con pytest
pytest tests/
```

### Debugging Lambda Local

```bash
# Usar AWS SAM CLI
sam local start-api -t template.yaml
```

## 📖 Documentación Adicional

- [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Especificación OpenAPI
- [AUTHENTICATION.md](../AUTHENTICATION.md) - Autenticación JWT
- [DEPLOYMENT_AWS.md](../DEPLOYMENT_AWS.md) - Guía de despliegue completa

## 🤝 Integración con ProvesiWMS

Las funciones Lambda validan productos y clientes contra ProvesiWMS Django:

```python
# En crear_pedido.py
cliente = validate_cliente(cliente_id)  # GET /api/clientes/{id}/
producto = validate_producto(producto_id)  # GET /api/productos/{id}/
```

**Requisitos**:
- ProvesiWMS debe ser accesible desde Lambda (VPC peering o Internet)
- Endpoints deben devolver JSON con campos `id`, `nombre`, `precio` (productos), `stock` (productos)

## 🐛 Troubleshooting

### Error: "Unable to connect to MongoDB"

```bash
# Verificar MongoDB está corriendo
ssh -i keypair.pem ubuntu@$(terraform output -raw mongodb_public_ip)
sudo systemctl status mongod

# Verificar conectividad desde Lambda (security group)
aws ec2 describe-security-groups --group-ids $(terraform output -raw mongodb_sg_id)
```

### Error: "Function timeout"

Aumentar timeout en `lambda.tf`:

```hcl
resource "aws_lambda_function" "crear_pedido" {
  timeout = 60  # Cambiar de 30 a 60 segundos
}
```

### Error: "Invalid state transition"

Revisar la máquina de estados. Solo transiciones válidas permitidas:

```python
VALID_TRANSITIONS = {
    'pendiente': ['confirmado', 'cancelado'],
    'confirmado': ['en_preparacion', 'cancelado'],
    # ...
}
```

## 📊 Roadmap

- [ ] Autenticación JWT con API Gateway Authorizer
- [ ] Tests unitarios con pytest
- [ ] Tests de integración con moto (AWS mocking)
- [ ] CI/CD con GitHub Actions
- [ ] DocumentDB en vez de MongoDB EC2
- [ ] VPC PrivateLink para ProvesiWMS
- [ ] AWS Secrets Manager para credenciales
- [ ] Lambda Layers versionados
- [ ] Rollback automático en caso de errores

## 📄 Licencia

MIT License - Ver [LICENSE](../LICENSE)

## 👥 Autores

- Equipo Los-Arquitectonicos
- Proyecto: ProvesiWMS Inventario
