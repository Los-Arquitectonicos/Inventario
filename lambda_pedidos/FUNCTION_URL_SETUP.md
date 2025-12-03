# Configuración Lambda con Function URL

## 📦 Deployment en AWS Lambda

### 1. Crear el paquete de despliegue

```bash
cd lambda_pedidos

# Instalar dependencias del layer
cd layer
pip install -r requirements.txt -t python/ --upgrade
cd ..

# Crear ZIP del layer
cd layer
zip -r ../layer.zip python/
cd ..

# Crear ZIP del handler principal
zip handler.zip handler.py
```

### 2. Configurar Lambda en AWS Console

#### A. Subir Layer

1. Ve a **Lambda** → **Layers**
2. Click **Create layer**
   - **Name**: `pedidos-dependencies`
   - **Upload**: `layer.zip`
   - **Compatible runtimes**: Python 3.11, Python 3.12
3. Click **Create**

#### B. Actualizar función Lambda

1. Ve a **Lambda** → Functions → `manejador_pedidos`
2. **Code** tab:
   - Click **Upload from** → **.zip file**
   - Subir `handler.zip`
   - **Runtime settings** → Edit:
     - **Handler**: `handler.lambda_handler` ⚠️ IMPORTANTE
3. **Configuration** → **Layers**:
   - Click **Add a layer**
   - **Custom layers** → Selecciona `pedidos-dependencies`
   - Click **Add**

#### C. Configurar Variables de Entorno

1. **Configuration** → **Environment variables**
2. Agregar:
   - `MONGODB_URI`: `mongodb://172.31.69.60:27017/pedidos_db`
   - `PROVESI_API_URL`: `https://provesi-alb-2028908830.us-east-1.elb.amazonaws.com`

#### D. Configurar Timeout y Memoria

1. **Configuration** → **General configuration** → Edit
   - **Memory**: 256 MB
   - **Timeout**: 30 segundos
2. Click **Save**

### 3. Obtener Function URL

Tu Function URL actual es:
```
https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/
```

## 🧪 Pruebas

### Crear un pedido

```bash
curl -X POST https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "productos": [
      {"producto_id": 1, "cantidad": 2}
    ],
    "notas": "Entrega urgente"
  }'
```

### Listar todos los pedidos

```bash
curl https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos
```

### Listar pedidos con filtros

```bash
# Por cliente
curl "https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos?cliente_id=1"

# Por estado
curl "https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos?estado=pendiente"

# Combinado
curl "https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos?cliente_id=1&estado=pendiente"
```

### Obtener pedido específico

```bash
curl https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos/PED-000001
```

### Actualizar seguimiento

```bash
curl -X PUT https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws/pedidos/PED-000001/seguimiento \
  -H "Content-Type: application/json" \
  -d '{
    "nuevo_estado": "confirmado",
    "comentario": "Pedido confirmado por almacén"
  }'
```

## 🔗 Integración con Kong

### Configuración en kong.yaml

```yaml
services:
  - name: pedidos-lambda
    url: https://s4fah7sb5idis3qzs6i3kddkgq0lkrpy.lambda-url.us-east-1.on.aws
    routes:
      - name: pedidos-route
        paths:
          - /pedidos
        strip_path: false
```

### Probar a través de Kong

```bash
# A través de Kong HTTP
curl -X POST http://100.27.254.135:8000/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "productos": [{"producto_id": 1, "cantidad": 2}]
  }'

# A través de Kong HTTPS
curl -k -X POST https://100.27.254.135:8443/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "productos": [{"producto_id": 1, "cantidad": 2}]
  }'
```

## 📊 Endpoints Disponibles

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/pedidos` | Crear nuevo pedido |
| GET | `/pedidos` | Listar pedidos (con filtros opcionales) |
| GET | `/pedidos/{numero}` | Obtener pedido específico |
| PUT | `/pedidos/{numero}/seguimiento` | Actualizar seguimiento |

## 🔍 Troubleshooting

### Ver logs en CloudWatch

1. Ve a **CloudWatch** → **Log groups**
2. Busca `/aws/lambda/manejador_pedidos`
3. Revisa los últimos logs

### Errores comunes

#### "Import could not be resolved"
- Asegúrate de que el Layer esté agregado a la función
- Verifica que el Layer contenga la carpeta `python/` con los módulos

#### "Handler not found"
- Verifica que el handler sea `handler.lambda_handler`
- El archivo debe llamarse `handler.py` en el ZIP

#### "Cannot connect to MongoDB"
- Verifica la variable `MONGODB_URI`
- Asegúrate de que la IP de MongoDB sea correcta
- Verifica el Security Group de MongoDB permita tráfico desde Lambda

#### "Cannot validate productos/clientes"
- Verifica la variable `PROVESI_API_URL`
- Asegúrate de que el ALB esté accesible desde Lambda
- Verifica que Django esté corriendo

## 🚀 Estados del Pedido

```
PENDIENTE → CONFIRMADO → EN_PREPARACION → EN_CAMINO → ENTREGADO
     ↓           ↓              ↓
  CANCELADO   CANCELADO      CANCELADO
```

Estados válidos:
- `pendiente`: Pedido creado
- `confirmado`: Confirmado por ventas
- `en_preparacion`: En almacén preparándose
- `en_camino`: En ruta de entrega
- `entregado`: Completado
- `cancelado`: Cancelado en cualquier momento
