# 🚀 Despliegue desde AWS CloudShell

Guía paso a paso para desplegar Lambda Pedidos desde **AWS CloudShell**.

## 📋 Pre-requisitos

1. Acceso a AWS Console
2. Permisos IAM para:
   - Lambda, API Gateway, EC2, IAM, CloudWatch
3. VPC con subnet (anotar IDs)
4. EC2 Key Pair creado (anotar nombre)

## 🔧 Paso 1: Abrir CloudShell

1. Ve a **AWS Console** (https://console.aws.amazon.com)
2. Haz clic en el ícono **CloudShell** (>_) en la barra superior derecha
3. Espera a que se inicie (toma ~30 segundos la primera vez)

## 📦 Paso 2: Clonar el Repositorio

En **CloudShell**:

```bash
git clone -b servicediscovery https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario/lambda_pedidos
```

## 🔑 Paso 3: Obtener IDs de tu Infraestructura

Ejecuta estos comandos en CloudShell para obtener tus IDs:

```bash
# 1. Obtener VPC ID
aws ec2 describe-vpcs --query 'Vpcs[0].VpcId' --output text

# 2. Obtener Subnet ID (pública preferiblemente)
aws ec2 describe-subnets --query 'Subnets[0].SubnetId' --output text

# 3. Listar Key Pairs disponibles
aws ec2 describe-key-pairs --query 'KeyPairs[*].KeyName' --output table

# 4. Obtener región actual
aws configure get region || echo "us-east-1"
```

**Anota estos valores:**
- VPC ID: `vpc-xxxxxxxxx`
- Subnet ID: `subnet-xxxxxxxxx`
- Key Name: `labsuser` (o el que tengas)
- Region: `us-east-1` (o la que uses)

## ⚙️ Paso 4: Configurar Variables

Crea el archivo `terraform/terraform.tfvars`:

```bash
cat > terraform/terraform.tfvars <<'EOF'
aws_region      = "us-east-1"
provesi_api_url = "http://34.204.191.209:8000"
key_name        = "labsuser"
vpc_id          = "vpc-XXXXXXXX"
subnet_id       = "subnet-XXXXXXXX"
EOF
```

**⚠️ IMPORTANTE:** Reemplaza los valores con los que anotaste arriba.

Verifica el contenido:

```bash
cat terraform/terraform.tfvars
```

## 📦 Paso 5: Empaquetar Funciones

```bash
./scripts/package.sh
```

Esto genera:
- `layer.zip` (~2-5 MB)
- `functions/crear_pedido.zip`
- `functions/consultar_pedido.zip`
- `functions/seguir_pedido.zip`

Verifica:
```bash
ls -lh *.zip functions/*.zip
```

## 🚀 Paso 6: Desplegar con Terraform

```bash
./scripts/deploy.sh
```

El script:
1. ✅ Verifica requisitos (Terraform ya está en CloudShell)
2. 📦 Valida archivos empaquetados
3. 🔧 Inicializa Terraform
4. 📋 Muestra el plan de ejecución
5. ⚠️ Te pide confirmación (escribe `yes`)
6. 🚀 Despliega infraestructura (~5-7 minutos)
7. 📊 Muestra URLs y outputs

**Tiempo total:** 5-7 minutos

## 📊 Paso 7: Ver los Outputs

Al finalizar, verás algo como:

```
Outputs:

api_gateway_url = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/pedidos"
mongodb_private_ip = "10.0.1.123"
mongodb_public_ip = "54.123.45.67"

endpoints = {
  crear_pedido = "POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/pedidos"
  listar_pedidos = "GET  https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/pedidos"
  ...
}
```

**Anota la URL del API Gateway.**

## 🧪 Paso 8: Probar los Endpoints

Espera **3 minutos** para que MongoDB se inicialice, luego:

```bash
./scripts/test_endpoints.sh
```

O prueba manualmente:

```bash
# Obtener la URL
API_URL=$(cd terraform && terraform output -raw api_gateway_url)

# Crear un pedido
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 1,
    "productos": [
      {"producto_id": 1, "cantidad": 10}
    ]
  }' | jq .
```

## 📊 Paso 9: Ver Logs en CloudWatch

Desde CloudShell:

```bash
# Ver logs de crear_pedido en tiempo real
aws logs tail /aws/lambda/pedidos-crear --follow

# O desde otro terminal CloudShell
aws logs tail /aws/apigateway/pedidos-api --follow
```

O desde la **AWS Console**:
1. Ve a **CloudWatch** → **Log Groups**
2. Busca `/aws/lambda/pedidos-crear`
3. Haz clic para ver logs en tiempo real

## 🔍 Troubleshooting

### Error: "No space left on device"

CloudShell tiene 1GB de storage. Limpia:

```bash
# Eliminar archivos temporales
rm -rf ~/.cache/pip
rm lambda_pedidos.tar.gz

# O reinicia CloudShell (Actions → Delete)
```

### Error: "UnauthorizedOperation"

Tu usuario IAM no tiene permisos. Necesitas:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "lambda:*",
      "apigateway:*",
      "ec2:*",
      "iam:*",
      "logs:*"
    ],
    "Resource": "*"
  }]
}
```

### Error: "Invalid subnet"

La subnet debe estar en la misma VPC. Verifica:

```bash
aws ec2 describe-subnets --subnet-ids subnet-XXXXXXXX
```

### MongoDB no responde

Espera 3-5 minutos después del deploy. Verifica:

```bash
# Ver logs de inicialización de EC2
INSTANCE_ID=$(cd terraform && terraform output -json | jq -r '.mongodb_instance_id.value')
aws ec2 get-console-output --instance-id $INSTANCE_ID
```

## 🧹 Paso 10: Limpiar Recursos (Opcional)

Para destruir toda la infraestructura:

```bash
cd terraform
terraform destroy
```

Escribe `yes` cuando te lo pida.

**Esto elimina:**
- 3 Funciones Lambda
- Lambda Layer
- API Gateway
- Instancia EC2 MongoDB
- Security Groups
- IAM Roles
- CloudWatch Logs

## 💡 Tips para CloudShell

### Persistencia

CloudShell mantiene el directorio `$HOME` pero tiene límite de 1GB. Si sales y vuelves:

```bash
cd Inventario/lambda_pedidos
# Todo sigue ahí, o puedes hacer git pull para actualizar
```

### Múltiples Regiones

CloudShell es **regional**. Si cambias de región (arriba a la derecha), tendrás un ambiente diferente.

### Timeout

CloudShell se desconecta tras 20 minutos de inactividad. Tu código permanece, solo reconéctate.

### Actualizar Código

Si haces cambios en GitHub:

```bash
cd ~/Inventario
git pull origin servicediscovery
cd lambda_pedidos
./scripts/package.sh
./scripts/deploy.sh
```

## 📚 Comandos Útiles

```bash
# Ver estado de Terraform
cd terraform
terraform show

# Ver outputs sin redesplegar
terraform output

# Ver solo la URL del API
terraform output -raw api_gateway_url

# Actualizar solo una función Lambda
terraform apply -target=aws_lambda_function.crear_pedido

# Ver logs de deploy
tail -f terraform.log
```

## 🎯 Checklist de Despliegue

- [ ] Abrir CloudShell
- [ ] Clonar repositorio: `git clone -b servicediscovery https://github.com/Los-Arquitectonicos/Inventario.git`
- [ ] Obtener VPC ID, Subnet ID, Key Name
- [ ] Crear `terraform/terraform.tfvars` con valores correctos
- [ ] Ejecutar `./scripts/package.sh`
- [ ] Ejecutar `./scripts/deploy.sh`
- [ ] Anotar URL del API Gateway
- [ ] Esperar 3 minutos para MongoDB
- [ ] Ejecutar `./scripts/test_endpoints.sh`
- [ ] Verificar logs en CloudWatch

## 🆘 Soporte

Si algo falla:

1. **Revisa los logs de Terraform:**
   ```bash
   cd terraform
   terraform show
   ```

2. **Revisa los logs de Lambda:**
   ```bash
   aws logs tail /aws/lambda/pedidos-crear --follow
   ```

3. **Verifica la instancia MongoDB:**
   ```bash
   INSTANCE_ID=$(cd terraform && terraform output -json | jq -r '.mongodb_instance_id.value')
   aws ec2 describe-instance-status --instance-ids $INSTANCE_ID
   ```

4. **Destruye y vuelve a desplegar:**
   ```bash
   cd terraform
   terraform destroy
   # Luego vuelve a ejecutar deploy.sh
   ```

---

**Costo estimado:** ~$15-20 USD/mes (instancia t3.small + 1M requests Lambda)

**Región recomendada:** us-east-1 (más económica y con todos los servicios)
