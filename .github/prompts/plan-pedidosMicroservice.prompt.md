# Plan: Microservicio de Gestión de Pedidos con FastAPI y MongoDB

Este plan detalla la extracción de la funcionalidad de pedidos de ProvesiWMS hacia un microservicio independiente usando FastAPI y MongoDB, con integración completa a Kong API Gateway y pruebas de desempeño con Locust.

## Contexto

La aplicación ProvesiWMS actualmente maneja inventarios y pedidos en un monolito Django con PostgreSQL. Se requiere extraer la gestión de pedidos a un microservicio independiente con las siguientes características:

- **Framework**: FastAPI (no Django)
- **Base de datos**: MongoDB (no PostgreSQL)
- **Autenticación**: Sin autenticación (público)
- **Funcionalidades**: Crear, consultar y seguir progreso de pedidos con timestamps
- **Infraestructura**: 2 instancias EC2 nuevas (aplicación + MongoDB)
- **Integración**: Kong API Gateway en ruta `/pedidos`

## Restricciones y Decisiones

### ✅ Confirmado
- ❌ **No migración de datos**: Empezar con base de datos vacía
- ✅ **Consulta de stock**: Llamar a InventarioWMS API para verificar disponibilidad
- ❌ **No reducción de stock**: Los pedidos NO reducen el inventario automáticamente
- ✅ **Arquitectura simple**: Sin transacciones distribuidas complejas (Saga simplificado)
- ✅ **Solo 2 instancias EC2**: MongoDB + Pedidos Service
- ✅ **Sin autenticación**: Endpoints públicos (sin JWT)
- **URL de InventarioWMS**: Usar IP privada de Django para consultas internas
- **Manejo de productos inexistentes**: Retornar error 400 si producto no existe en inventario



## Arquitectura Propuesta

```
Internet → ALB (HTTPS/443) → Kong Gateway (3.238.225.18:8443)
                                    ├→ /inventario → Django ProvesiWMS (productos, bodegas, clientes)
                                    ├→ /notifications → FastAPI Notifications (MongoDB)
                                    └→ /pedidos → FastAPI Orders Service (NUEVO)
                                                      ↓
                                                  MongoDB Orders DB (puerto 27017)
```

### Flujo de Creación de Pedido

```
1. Cliente → POST /pedidos {"cliente_id": 1, "productos": [{"producto_id": 5, "cantidad": 3}]}
              ↓
2. Orders Service → Validar request (Pydantic)
              ↓
3. Orders Service → GET https://{DJANGO_IP}:8080/api/productos/5
              ↓
4. Django InventarioWMS → {"id": 5, "nombre": "Camiseta", "stock": 10, "precio_venta": 25.00}
              ↓
5. Orders Service → Validar stock >= cantidad (10 >= 3 ✓)
              ↓
6. Orders Service → Guardar en MongoDB con precio snapshot
              ↓
7. Orders Service → 201 Created {"pedido_id": "...", "numero_pedido": "PED-000001", ...}
```

## Estructura del Proyecto

```
Inventario/
├── pedidos_service/                    # NUEVO: Microservicio de Pedidos
│   ├── main.py                         # FastAPI application entrypoint
│   ├── config.py                       # Configuración (MongoDB URI, Django API URL)
│   ├── database.py                     # MongoDB connection y cliente
│   ├── models/
│   │   ├── __init__.py
│   │   ├── order.py                    # Modelos MongoDB (Order, OrderProduct)
│   │   └── enums.py                    # OrderStatus enum
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── order.py                    # Pydantic schemas (CreateOrder, OrderResponse)
│   │   └── product.py                  # Product schema para validación
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── orders.py                   # CRUD endpoints de pedidos
│   │   └── health.py                   # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── order_service.py            # Business logic de pedidos
│   │   └── inventory_client.py         # Cliente HTTP para InventarioWMS
│   ├── requirements.txt                # Dependencies
│   ├── start_service.sh                # Script de inicio
│   ├── restart_service.sh              # Script de reinicio
│   └── README.md                       # Documentación del servicio
│
├── terraform/
│   ├── main.tf                         # [MODIFICAR] Variables globales
│   ├── deployment.tf                   # [MODIFICAR] Agregar instancias pedidos
│   ├── variables.tf                    # [MODIFICAR] Variables nuevas
│   └── outputs.tf                      # [MODIFICAR] Outputs de IPs
│
├── kong/
│   └── kong.yml                        # [MODIFICAR] Agregar route /pedidos
│
├── tests/
│   └── load_testing/
│       ├── pedidos_locustfile.py       # NUEVO: Pruebas de carga Locust
│       └── README.md                   # Documentación de pruebas
│
└── ProvesiWMS/
    └── inventario/
        ├── models.py                    # [MODIFICAR] Eliminar modelos de pedidos
        ├── views.py                     # [MODIFICAR] Eliminar vistas de pedidos
        ├── urls.py                      # [MODIFICAR] Eliminar URLs de pedidos
        ├── admin.py                     # [MODIFICAR] Eliminar admin de pedidos
        └── templates/inventario/
            └── pedidos/                 # [ELIMINAR] Todo el directorio
```

## Modelos de Datos

### MongoDB Schema (pedidos_service)

#### Collection: `orders`

```json
{
  "_id": ObjectId("..."),
  "numero_pedido": "PED-000001",
  "estado": "pendiente",
  "fecha_creacion": ISODate("2025-12-03T10:30:00Z"),
  "fecha_completado": null,
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
    },
    {
      "producto_id": 12,
      "nombre": "Pantalón Negro",
      "cantidad": 1,
      "precio_unitario": 45.50
    }
  ],
  "total": 120.50,
  "timestamps": {
    "pendiente": ISODate("2025-12-03T10:30:00Z"),
    "preparando": null,
    "listo": null,
    "enviado": null,
    "entregado": null,
    "cancelado": null
  },
  "notas": ""
}
```

### Estados de Pedido

```python
class OrderStatus(str, Enum):
    PENDIENTE = "pendiente"      # Pedido creado, esperando procesamiento
    PREPARANDO = "preparando"    # En proceso de alistamiento
    LISTO = "listo"              # Listo para envío
    ENVIADO = "enviado"          # Enviado al cliente
    ENTREGADO = "entregado"      # Entregado y completado
    CANCELADO = "cancelado"      # Cancelado por alguna razón
```

### Transiciones de Estado Válidas

```
pendiente → preparando, cancelado
preparando → listo, cancelado
listo → enviado, cancelado
enviado → entregado
entregado → (final)
cancelado → (final)
```

## API Endpoints del Microservicio

### Health Check

```http
GET /health
```

**Response 200**:
```json
{
  "status": "healthy",
  "service": "pedidos-service",
  "mongodb": "connected",
  "timestamp": "2025-12-03T10:30:00Z"
}
```

### Listar Pedidos

```http
GET /pedidos?estado=pendiente&cliente_id=1&limit=50&offset=0
```

**Query Parameters**:
- `estado` (optional): Filtrar por estado
- `cliente_id` (optional): Filtrar por cliente
- `fecha_desde` (optional): ISO date - Filtrar desde fecha
- `fecha_hasta` (optional): ISO date - Filtrar hasta fecha
- `limit` (optional, default=50, max=100): Paginación
- `offset` (optional, default=0): Paginación

**Response 200**:
```json
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "pedidos": [
    {
      "id": "674f3a1b2e9c8d4f1a2b3c4d",
      "numero_pedido": "PED-000001",
      "estado": "pendiente",
      "fecha_creacion": "2025-12-03T10:30:00Z",
      "fecha_completado": null,
      "cliente_id": 1,
      "cliente_nombre": "Juan Pérez",
      "total": 120.50,
      "cantidad_productos": 2
    }
  ]
}
```

### Obtener Detalle de Pedido

```http
GET /pedidos/{pedido_id}
```

**Response 200**:
```json
{
  "id": "674f3a1b2e9c8d4f1a2b3c4d",
  "numero_pedido": "PED-000001",
  "estado": "pendiente",
  "fecha_creacion": "2025-12-03T10:30:00Z",
  "fecha_completado": null,
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
  "total": 120.50,
  "timestamps": {
    "pendiente": "2025-12-03T10:30:00Z",
    "preparando": null,
    "listo": null,
    "enviado": null,
    "entregado": null,
    "cancelado": null
  },
  "puede_cancelar": true,
  "notas": ""
}
```

**Response 404**:
```json
{
  "detail": "Pedido no encontrado"
}
```

### Crear Pedido

```http
POST /pedidos
Content-Type: application/json

{
  "cliente_id": 1,
  "productos": [
    {
      "producto_id": 5,
      "cantidad": 3
    },
    {
      "producto_id": 12,
      "cantidad": 1
    }
  ],
  "notas": "Entregar antes de las 5pm"
}
```

**Validaciones**:
1. `cliente_id` es requerido y debe ser entero positivo
2. `productos` debe tener al menos 1 producto
3. `cantidad` debe ser mayor a 0
4. Para cada producto:
   - Verificar que existe en InventarioWMS
   - Verificar que `stock >= cantidad`
   - Capturar `precio_venta` como snapshot

**Response 201**:
```json
{
  "id": "674f3a1b2e9c8d4f1a2b3c4d",
  "numero_pedido": "PED-000001",
  "estado": "pendiente",
  "fecha_creacion": "2025-12-03T10:30:00Z",
  "mensaje": "Pedido creado exitosamente"
}
```

**Response 400** (Stock insuficiente):
```json
{
  "detail": "Stock insuficiente para producto 'Camiseta Azul'. Disponible: 2, Requerido: 3"
}
```

**Response 400** (Producto no existe):
```json
{
  "detail": "Producto con ID 999 no encontrado en inventario"
}
```

**Response 502** (Error comunicación con InventarioWMS):
```json
{
  "detail": "Error al comunicarse con el servicio de inventario"
}
```

### Actualizar Estado de Pedido

```http
PUT /pedidos/{pedido_id}/estado
Content-Type: application/json

{
  "estado": "preparando"
}
```

**Validaciones**:
1. `estado` debe ser uno de los valores válidos del enum
2. Transición de estado debe ser válida según state machine
3. Si estado es "entregado", se registra `fecha_completado`

**Response 200**:
```json
{
  "id": "674f3a1b2e9c8d4f1a2b3c4d",
  "numero_pedido": "PED-000001",
  "estado": "preparando",
  "estado_anterior": "pendiente",
  "fecha_actualizacion": "2025-12-03T11:00:00Z",
  "mensaje": "Estado actualizado exitosamente"
}
```

**Response 400** (Transición inválida):
```json
{
  "detail": "Transición inválida: no se puede cambiar de 'enviado' a 'pendiente'"
}
```

**Response 404**:
```json
{
  "detail": "Pedido no encontrado"
}
```

### Cancelar Pedido

```http
DELETE /pedidos/{pedido_id}
```

**Validaciones**:
1. Solo se puede cancelar si estado es `pendiente` o `preparando`

**Response 200**:
```json
{
  "id": "674f3a1b2e9c8d4f1a2b3c4d",
  "numero_pedido": "PED-000001",
  "estado": "cancelado",
  "mensaje": "Pedido cancelado exitosamente"
}
```

**Response 400** (No se puede cancelar):
```json
{
  "detail": "No se puede cancelar un pedido en estado 'enviado'"
}
```

## Comunicación con InventarioWMS

### Endpoint de Django a Consumir

```http
GET /api/productos/{producto_id}
Authorization: Bearer {token_opcional}
```

**Response de Django**:
```json
{
  "id": 5,
  "codigo": "CAM-001",
  "nombre": "Camiseta Azul",
  "descripcion": "Camiseta 100% algodón",
  "precio_venta": 25.00,
  "stock": 10,
  "categoria": "Ropa",
  "es_activo": true
}
```

### Cliente HTTP en Pedidos Service

```python
# services/inventory_client.py

import httpx
from typing import Optional, Dict
from config import settings

class InventoryClient:
    def __init__(self):
        self.base_url = settings.DJANGO_API_URL
        self.timeout = 5.0
    
    async def get_product(self, producto_id: int) -> Optional[Dict]:
        """Consulta información de un producto en InventarioWMS"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/productos/{producto_id}"
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except httpx.RequestError:
            raise Exception("Error de comunicación con servicio de inventario")
    
    async def validate_stock(self, producto_id: int, cantidad: int) -> tuple[bool, str, float]:
        """
        Valida que haya stock suficiente para un producto
        Returns: (stock_ok, nombre_producto, precio_unitario)
        """
        producto = await self.get_product(producto_id)
        
        if not producto:
            raise ValueError(f"Producto con ID {producto_id} no encontrado")
        
        stock_disponible = producto.get("stock", 0)
        if stock_disponible < cantidad:
            return False, producto["nombre"], producto["precio_venta"]
        
        return True, producto["nombre"], producto["precio_venta"]
```

## Infraestructura Terraform

### Variables Nuevas (terraform/variables.tf)

```hcl
# ===================================
# PEDIDOS SERVICE VARIABLES
# ===================================

variable "pedidos_instance_type" {
  description = "EC2 instance type for Orders Service"
  type        = string
  default     = "t3.small"
}

variable "mongodb_instance_type" {
  description = "EC2 instance type for MongoDB"
  type        = string
  default     = "t3.small"
}

variable "mongodb_port" {
  description = "MongoDB port"
  type        = number
  default     = 27017
}

variable "pedidos_port" {
  description = "Orders service port"
  type        = number
  default     = 8002
}
```

### Instancia MongoDB (terraform/deployment.tf)

```hcl
# ===================================
# MONGODB INSTANCE FOR ORDERS
# ===================================

resource "aws_security_group" "mongodb_orders" {
  name        = "${var.project_prefix}-mongodb-orders-sg"
  description = "Security group for MongoDB Orders database"
  
  # MongoDB port from Orders Service
  ingress {
    description     = "MongoDB from Orders Service"
    from_port       = var.mongodb_port
    to_port         = var.mongodb_port
    protocol        = "tcp"
    security_groups = [aws_security_group.pedidos.id]
  }
  
  # SSH for management
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_prefix}-mongodb-orders-sg"
  }
}

resource "aws_instance" "mongodb_orders" {
  ami                    = "ami-0e2c8caa4b6378d8c"  # Ubuntu 24.04 LTS
  instance_type          = var.mongodb_instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.mongodb_orders.id]
  
  user_data = <<-EOT
#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y gnupg curl

# Install MongoDB 7.0
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  tee /etc/apt/sources.list.d/mongodb-org-7.0.list

apt-get update
apt-get install -y mongodb-org

# Configure MongoDB to listen on all interfaces
sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf

# Start MongoDB
systemctl start mongod
systemctl enable mongod

# Create orders database
sleep 5
mongosh --eval "use orders_db; db.createCollection('orders');"

# Create indexes
mongosh orders_db --eval '
  db.orders.createIndex({ "numero_pedido": 1 }, { unique: true });
  db.orders.createIndex({ "cliente_id": 1 });
  db.orders.createIndex({ "estado": 1 });
  db.orders.createIndex({ "fecha_creacion": -1 });
'

echo "MongoDB setup completed" > /home/ubuntu/mongodb_setup.log
EOT
  
  tags = {
    Name = "${var.project_prefix}-mongodb-orders"
    Role = "database"
  }
}
```

### Instancia Pedidos Service (terraform/deployment.tf)

```hcl
# ===================================
# ORDERS SERVICE INSTANCE
# ===================================

resource "aws_security_group" "pedidos" {
  name        = "${var.project_prefix}-pedidos-sg"
  description = "Security group for Orders Service"
  
  # HTTP from Kong
  ingress {
    description     = "Orders service from Kong"
    from_port       = var.pedidos_port
    to_port         = var.pedidos_port
    protocol        = "tcp"
    security_groups = [aws_security_group.kong.id]
  }
  
  # SSH for management
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_prefix}-pedidos-sg"
  }
}

resource "aws_instance" "pedidos" {
  ami                    = "ami-0e2c8caa4b6378d8c"  # Ubuntu 24.04 LTS
  instance_type          = var.pedidos_instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.pedidos.id]
  
  depends_on = [
    aws_instance.mongodb_orders,
    aws_instance.django_app_1
  ]
  
  user_data = <<-EOT
#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y python3 python3-pip python3-venv git

# Clone repository
cd /home/ubuntu
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario
git checkout servicediscovery

# Setup pedidos service
cd pedidos_service
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create environment file
cat > .env <<ENV
MONGODB_URI=mongodb://${aws_instance.mongodb_orders.private_ip}:${var.mongodb_port}/orders_db
DJANGO_API_URL=http://${aws_instance.django_app_1.private_ip}:8080
SERVICE_PORT=${var.pedidos_port}
ENV

# Create systemd service
cat > /etc/systemd/system/pedidos.service <<SERVICE
[Unit]
Description=Pedidos FastAPI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Inventario/pedidos_service
Environment="PATH=/home/ubuntu/Inventario/pedidos_service/venv/bin"
ExecStart=/home/ubuntu/Inventario/pedidos_service/venv/bin/uvicorn main:app --host 0.0.0.0 --port ${var.pedidos_port}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Start service
systemctl daemon-reload
systemctl start pedidos
systemctl enable pedidos

# Wait for service to be ready
sleep 10

# Test health endpoint
curl -f http://localhost:${var.pedidos_port}/health || echo "Health check failed"

echo "Pedidos service setup completed" > /home/ubuntu/pedidos_setup.log
EOT
  
  tags = {
    Name = "${var.project_prefix}-pedidos"
    Role = "microservice"
  }
}
```

### Outputs (terraform/outputs.tf)

```hcl
# ===================================
# PEDIDOS SERVICE OUTPUTS
# ===================================

output "mongodb_orders_private_ip" {
  description = "Private IP of MongoDB Orders instance"
  value       = aws_instance.mongodb_orders.private_ip
}

output "mongodb_orders_public_ip" {
  description = "Public IP of MongoDB Orders instance"
  value       = aws_instance.mongodb_orders.public_ip
}

output "pedidos_service_private_ip" {
  description = "Private IP of Orders Service instance"
  value       = aws_instance.pedidos.private_ip
}

output "pedidos_service_public_ip" {
  description = "Public IP of Orders Service instance"
  value       = aws_instance.pedidos.public_ip
}

output "pedidos_service_url" {
  description = "Internal URL of Orders Service"
  value       = "http://${aws_instance.pedidos.private_ip}:${var.pedidos_port}"
}

output "pedidos_health_check" {
  description = "Health check command for Orders Service"
  value       = "curl http://${aws_instance.pedidos.private_ip}:${var.pedidos_port}/health"
}
```

## Integración Kong Gateway

### Modificar kong.yml

```yaml
# Agregar al final del archivo kong/kong.yml

# ==========================================
# SERVICE: ORDERS (PEDIDOS)
# ==========================================
services:
  - name: pedidos
    url: http://${PEDIDOS_PRIVATE_IP}:8002
    retries: 3
    connect_timeout: 5000
    routes:
      - name: pedidos-routes
        paths:
          - /pedidos
        strip_path: false
        preserve_host: true
    plugins:
      - name: rate-limiting
        config:
          minute: 150
          policy: local
      - name: cors
        config:
          origins: ["*"]
          credentials: true
          max_age: 3600
```

**Nota**: No incluir plugin `jwt` ya que el servicio NO requiere autenticación.

## Pruebas de Carga con Locust

### tests/load_testing/pedidos_locustfile.py

```python
"""
Pruebas de carga para el microservicio de Pedidos

Ejecutar:
  locust -f pedidos_locustfile.py --host=https://3.238.225.18:8443

Escenarios:
  1. Crear pedidos (POST /pedidos)
  2. Listar pedidos (GET /pedidos)
  3. Obtener detalle (GET /pedidos/{id})
  4. Actualizar estado (PUT /pedidos/{id}/estado)
"""

from locust import HttpUser, task, between
import random
import json

class PedidosUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup: crear algunos pedidos de prueba"""
        self.pedido_ids = []
        self.cliente_ids = list(range(1, 11))  # Asumiendo 10 clientes en sistema
        self.producto_ids = list(range(1, 21))  # Asumiendo 20 productos
        
        # Verificar salud del servicio
        response = self.client.get("/pedidos/health", verify=False)
        if response.status_code == 200:
            print("✅ Servicio de pedidos está saludable")
    
    @task(3)
    def crear_pedido(self):
        """Crear un nuevo pedido (peso 3 - más frecuente)"""
        cliente_id = random.choice(self.cliente_ids)
        num_productos = random.randint(1, 5)
        
        productos = []
        for _ in range(num_productos):
            productos.append({
                "producto_id": random.choice(self.producto_ids),
                "cantidad": random.randint(1, 10)
            })
        
        payload = {
            "cliente_id": cliente_id,
            "productos": productos,
            "notas": f"Pedido de prueba - Locust {random.randint(1000, 9999)}"
        }
        
        with self.client.post(
            "/pedidos",
            json=payload,
            catch_response=True,
            verify=False,
            name="/pedidos [CREATE]"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.pedido_ids.append(data["id"])
                response.success()
            elif response.status_code == 400:
                # Stock insuficiente es esperado en pruebas
                response.success()
            else:
                response.failure(f"Error {response.status_code}: {response.text}")
    
    @task(5)
    def listar_pedidos(self):
        """Listar pedidos con filtros (peso 5 - muy frecuente)"""
        params = {}
        
        # 50% de las veces usar filtros
        if random.random() > 0.5:
            estados = ["pendiente", "preparando", "listo", "enviado", "entregado"]
            params["estado"] = random.choice(estados)
        
        if random.random() > 0.7:
            params["cliente_id"] = random.choice(self.cliente_ids)
        
        params["limit"] = random.choice([10, 25, 50])
        
        with self.client.get(
            "/pedidos",
            params=params,
            catch_response=True,
            verify=False,
            name="/pedidos [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error {response.status_code}")
    
    @task(4)
    def obtener_detalle(self):
        """Obtener detalle de un pedido (peso 4 - frecuente)"""
        if not self.pedido_ids:
            return
        
        pedido_id = random.choice(self.pedido_ids)
        
        with self.client.get(
            f"/pedidos/{pedido_id}",
            catch_response=True,
            verify=False,
            name="/pedidos/{id} [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Pedido fue eliminado, remover de lista
                self.pedido_ids.remove(pedido_id)
                response.success()
            else:
                response.failure(f"Error {response.status_code}")
    
    @task(2)
    def actualizar_estado(self):
        """Actualizar estado de un pedido (peso 2 - menos frecuente)"""
        if not self.pedido_ids:
            return
        
        pedido_id = random.choice(self.pedido_ids)
        estados = ["preparando", "listo", "enviado", "entregado"]
        nuevo_estado = random.choice(estados)
        
        payload = {"estado": nuevo_estado}
        
        with self.client.put(
            f"/pedidos/{pedido_id}/estado",
            json=payload,
            catch_response=True,
            verify=False,
            name="/pedidos/{id}/estado [UPDATE]"
        ) as response:
            if response.status_code in [200, 400]:
                # 400 por transición inválida es esperado
                response.success()
            else:
                response.failure(f"Error {response.status_code}")
    
    @task(1)
    def cancelar_pedido(self):
        """Cancelar un pedido (peso 1 - poco frecuente)"""
        if not self.pedido_ids:
            return
        
        pedido_id = random.choice(self.pedido_ids)
        
        with self.client.delete(
            f"/pedidos/{pedido_id}",
            catch_response=True,
            verify=False,
            name="/pedidos/{id} [DELETE]"
        ) as response:
            if response.status_code in [200, 400]:
                # 400 si no se puede cancelar es esperado
                if response.status_code == 200:
                    self.pedido_ids.remove(pedido_id)
                response.success()
            else:
                response.failure(f"Error {response.status_code}")


class PedidosStressUser(HttpUser):
    """Usuario para pruebas de estrés - operaciones más pesadas"""
    wait_time = between(0.5, 1.5)
    
    @task
    def crear_pedido_grande(self):
        """Crear pedidos con muchos productos"""
        cliente_id = random.randint(1, 10)
        
        productos = []
        for _ in range(random.randint(10, 20)):
            productos.append({
                "producto_id": random.randint(1, 20),
                "cantidad": random.randint(5, 20)
            })
        
        payload = {
            "cliente_id": cliente_id,
            "productos": productos,
            "notas": "Pedido grande de prueba"
        }
        
        self.client.post("/pedidos", json=payload, verify=False)
```

### tests/load_testing/README.md

```markdown
# Pruebas de Carga - Microservicio de Pedidos

## Requisitos

```bash
pip install locust
```

## Ejecutar Pruebas

### Prueba Básica (UI Web)
```bash
cd tests/load_testing
locust -f pedidos_locustfile.py --host=https://3.238.225.18:8443
```

Abrir navegador en http://localhost:8089

### Prueba desde Línea de Comando
```bash
# 100 usuarios, 10 usuarios/segundo, 5 minutos
locust -f pedidos_locustfile.py \
  --host=https://3.238.225.18:8443 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

## Escenarios de Prueba

### 1. Load Test Normal
- **Usuarios**: 50
- **Spawn rate**: 5/s
- **Duración**: 10 minutos
- **Objetivo**: P95 latency < 200ms, 0% error rate

### 2. Stress Test
- **Usuarios**: 200
- **Spawn rate**: 20/s
- **Duración**: 5 minutos
- **Objetivo**: Identificar punto de quiebre

### 3. Spike Test
- **Usuarios**: 0 → 500 → 0
- **Duración**: 30 segundos pico
- **Objetivo**: Recuperación automática

## Métricas Objetivo

| Métrica | Objetivo |
|---------|----------|
| P50 Latency | < 100ms |
| P95 Latency | < 200ms |
| P99 Latency | < 500ms |
| Throughput | > 100 req/s |
| Error Rate | < 1% |
| Success Rate | > 99% |

## Análisis de Resultados

Después de ejecutar, revisar:
- `/pedidos [CREATE]` - Debe ser la operación más lenta
- `/pedidos [LIST]` - Debe ser la más rápida (MongoDB index)
- Error rate en stock insuficiente es normal
- Monitorear memoria en MongoDB y FastAPI instances
```

## Eliminación de Código de Pedidos en Django

### Modelos a Eliminar (inventario/models.py)

Eliminar completamente:
- `Pedido` (líneas 198-235)
- `PedidoProducto` (líneas 237-248)
- `PedidoArticulo` (líneas 250-257)
- `DevolucionPedido` (líneas 266-273)
- `ReclamoPedido` (líneas 275-282)
- `AlistamientoPedido` (líneas 284-291)
- `EmpaquePedido` (líneas 293-301)
- `VerificacionPedido` (líneas 303-311)
- `GuiaEnvioPedido` (líneas 313-321)
- `Factura` (líneas 323-336)

### Vistas a Eliminar (inventario/views.py)

Eliminar completamente:
- `PedidoListView` (líneas 484-503)
- `PedidoDetailView` (líneas 507-520)
- `CrearPedidoView` (líneas 524-583)
- `ActualizarEstadoPedido` (líneas 587-628)
- `pedido_detalle_api` (líneas 633-710)
- `pedido_total_api` (líneas 1236-1247)
- `pedidos_api_view` (líneas 1749-1870)

### URLs a Eliminar (inventario/urls.py)

Eliminar paths:
- `path('pedidos/', ...)`
- `path('pedidos/crear/', ...)`
- `path('pedidos/<int:pk>/', ...)`
- `path('pedidos/<int:pk>/actualizar-estado/', ...)`
- `path('api/pedidos/', ...)`
- `path('api/pedidos/<int:pedido_id>/', ...)`
- `path('api/pedidos/<int:pedido_id>/total/', ...)`

### Templates a Eliminar

Eliminar directorio completo:
- `templates/inventario/pedidos/`
  - `lista.html`
  - `detalle.html`
  - `crear.html`

### Admin a Actualizar (inventario/admin.py)

Eliminar registros:
- `admin.site.register(Pedido)`
- `admin.site.register(PedidoProducto)`
- `admin.site.register(PedidoArticulo)`
- Y todos los demás modelos de pedidos

### Tests a Eliminar (inventario/tests.py)

Eliminar todas las pruebas relacionadas con pedidos:
- `test_pedido_creation`
- `test_pedido_str`
- `test_calcular_total`
- `test_puede_cancelar`
- `test_marcar_entregado`
- `test_pedido_producto`
- `test_pedido_total_api`
- `test_pedido_api_crud`
- Etc.

## Pasos de Implementación

### Fase 1: Crear Microservicio (Día 1)
1. ✅ Crear estructura de directorios `pedidos_service/`
2. ✅ Implementar modelos Pydantic y MongoDB schemas
3. ✅ Implementar `inventory_client.py` para comunicación con Django
4. ✅ Implementar `order_service.py` con lógica de negocio
5. ✅ Implementar endpoints en `routes/orders.py`
6. ✅ Crear `main.py` y configurar FastAPI app
7. ✅ Crear `requirements.txt` y scripts de inicio
8. ✅ Crear tests unitarios básicos

### Fase 2: Infraestructura Terraform (Día 1-2)
1. ✅ Agregar variables en `variables.tf`
2. ✅ Crear security groups para MongoDB y Pedidos Service
3. ✅ Crear instancia MongoDB con user_data completo
4. ✅ Crear instancia Pedidos Service con user_data completo
5. ✅ Agregar outputs en `outputs.tf`
6. ✅ Probar despliegue: `terraform plan && terraform apply`

### Fase 3: Integración Kong (Día 2)
1. ✅ Actualizar `kong.yml` con servicio pedidos
2. ✅ Configurar route `/pedidos` sin autenticación
3. ✅ Agregar rate limiting
4. ✅ Recargar Kong: `sudo kong reload`
5. ✅ Probar endpoints a través de Kong

### Fase 4: Pruebas de Carga (Día 2-3)
1. ✅ Crear `pedidos_locustfile.py`
2. ✅ Ejecutar load test básico
3. ✅ Ejecutar stress test
4. ✅ Analizar métricas y ajustar configuración
5. ✅ Documentar resultados

### Fase 5: Limpieza Django (Día 3)
1. ✅ Backup de base de datos PostgreSQL
2. ✅ Eliminar modelos de pedidos
3. ✅ Eliminar vistas de pedidos
4. ✅ Eliminar URLs de pedidos
5. ✅ Eliminar templates de pedidos
6. ✅ Eliminar admin de pedidos
7. ✅ Eliminar tests de pedidos
8. ✅ Ejecutar `python manage.py makemigrations`
9. ✅ Ejecutar `python manage.py migrate`
10. ✅ Verificar que Django sigue funcionando correctamente

## Consideraciones de Seguridad

### Sin Autenticación
- **Decisión**: El servicio NO requiere autenticación JWT
- **Riesgo**: Endpoints públicos pueden ser abusados
- **Mitigación**: 
  - Rate limiting en Kong (150 req/min)
  - Validación estricta de inputs
  - Logging exhaustivo
  - Considerar agregar API key en el futuro

### Comunicación con InventarioWMS
- **Opción 1**: Sin autenticación (Django acepta llamadas internas)
- **Opción 2**: Token JWT de servicio a servicio
- **Recomendación**: Opción 1 inicialmente (red privada), Opción 2 para producción

## Monitoreo y Logging

### Logs en Pedidos Service
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/pedidos.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Métricas a Monitorear
1. **Latencia**:
   - P50, P95, P99 de cada endpoint
   - Latencia de llamadas a InventarioWMS
2. **Throughput**:
   - Requests por segundo
   - Pedidos creados por minuto
3. **Errores**:
   - Rate de errores 4xx y 5xx
   - Errores de comunicación con Django
   - Errores de MongoDB
4. **Recursos**:
   - CPU y memoria de instancias EC2
   - Conexiones a MongoDB
   - Tamaño de base de datos

## Próximos Pasos (Post-MVP)

### Mejoras Funcionales
1. **Notificaciones**: Integrar con servicio de notificaciones
2. **Webhooks**: Enviar eventos cuando cambia estado de pedido
3. **Auditoría**: Guardar historial de cambios de estado
4. **Búsqueda**: Implementar búsqueda por número de pedido, cliente
5. **Reportes**: Endpoint de estadísticas y reportes

### Mejoras Técnicas
1. **Cache**: Redis para listar pedidos frecuentes
2. **Event Sourcing**: Guardar todos los eventos de estado
3. **Circuit Breaker**: Para llamadas a InventarioWMS
4. **Retry Logic**: Reintentos con backoff exponencial
5. **Health Checks**: Checks más completos (MongoDB, Django connectivity)

### Mejoras de Infraestructura
1. **Alta Disponibilidad**: 2+ instancias de Pedidos Service con load balancer
2. **MongoDB Replica Set**: Para redundancia
3. **Backup Automático**: Snapshots diarios de MongoDB
4. **Monitoring**: CloudWatch + Grafana
5. **Alertas**: PagerDuty o SNS para errores críticos

## Checklist Final

### Pre-Deployment
- [ ] Código del microservicio completo y testeado
- [ ] Terraform configurations validadas
- [ ] Kong configuration actualizada
- [ ] Scripts de inicio probados localmente
- [ ] Variables de entorno documentadas

### Deployment
- [ ] `terraform apply` exitoso
- [ ] MongoDB iniciado y accesible
- [ ] Pedidos Service iniciado y saludable
- [ ] Kong route configurada y accesible
- [ ] Health checks pasando

### Post-Deployment
- [ ] Crear pedido de prueba exitoso
- [ ] Listar pedidos funciona
- [ ] Actualizar estado funciona
- [ ] Pruebas de carga ejecutadas
- [ ] Logs funcionando correctamente
- [ ] Django limpio de código de pedidos

### Validación Final
- [ ] Crear 10 pedidos diversos
- [ ] Verificar en MongoDB
- [ ] Probar todos los estados
- [ ] Verificar rate limiting
- [ ] Documentación actualizada
