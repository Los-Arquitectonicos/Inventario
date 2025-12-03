#!/bin/bash
# Script para desplegar infraestructura Terraform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

echo "=========================================="
echo "🚀 DESPLEGANDO LAMBDA PEDIDOS EN AWS"
echo "=========================================="

# ==========================================
# 1. VERIFICAR REQUISITOS
# ==========================================
echo ""
echo "1️⃣  Verificando requisitos..."

# Verificar Terraform
if ! command -v terraform &> /dev/null; then
  echo "❌ Error: Terraform no está instalado"
  echo "   Instálalo desde: https://www.terraform.io/downloads"
  exit 1
fi
echo "   ✅ Terraform: $(terraform version -json | jq -r '.terraform_version')"

# Verificar AWS CLI (CloudShell lo tiene preinstalado)
if ! command -v aws &> /dev/null; then
  echo "❌ Error: AWS CLI no está instalado"
  exit 1
fi
echo "   ✅ AWS CLI: $(aws --version 2>&1 | cut -d' ' -f1 || echo 'installed')"

# Verificar credenciales AWS (CloudShell tiene credenciales automáticas)
if ! aws sts get-caller-identity &> /dev/null; then
  echo "❌ Error: No se puede conectar a AWS"
  exit 1
fi
echo "   ✅ AWS Account: $(aws sts get-caller-identity --query Account --output text)"

# Verificar archivos empaquetados
if [ ! -f "$PROJECT_ROOT/layer.zip" ]; then
  echo "❌ Error: layer.zip no existe"
  echo "   Ejecuta primero: ./scripts/package.sh"
  exit 1
fi
echo "   ✅ layer.zip encontrado"

for func in crear_pedido consultar_pedido seguir_pedido; do
  if [ ! -f "$PROJECT_ROOT/functions/${func}.zip" ]; then
    echo "❌ Error: functions/${func}.zip no existe"
    echo "   Ejecuta primero: ./scripts/package.sh"
    exit 1
  fi
done
echo "   ✅ Funciones Lambda empaquetadas"

# ==========================================
# 2. VERIFICAR TERRAFORM VARS
# ==========================================
echo ""
echo "2️⃣  Verificando variables Terraform..."

if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
  echo "⚠️  Advertencia: terraform.tfvars no existe"
  echo ""
  echo "   Crea el archivo con tus valores:"
  echo ""
  echo "   cat > $TERRAFORM_DIR/terraform.tfvars <<EOF"
  echo "   aws_region          = \"us-east-1\""
  echo "   provesi_api_url     = \"http://tu-ip:8000\""
  echo "   key_name            = \"tu-keypair\""
  echo "   vpc_id              = \"vpc-xxxxxxxx\""
  echo "   subnet_id           = \"subnet-xxxxxxxx\""
  echo "   EOF"
  echo ""
  read -p "¿Deseas continuar sin terraform.tfvars? (y/N): " response
  if [[ ! "$response" =~ ^[Yy]$ ]]; then
    exit 0
  fi
else
  echo "   ✅ terraform.tfvars encontrado"
fi

# ==========================================
# 3. TERRAFORM INIT
# ==========================================
echo ""
echo "3️⃣  Inicializando Terraform..."

cd "$TERRAFORM_DIR"
terraform init

# ==========================================
# 4. TERRAFORM PLAN
# ==========================================
echo ""
echo "4️⃣  Generando plan de ejecución..."
echo ""

terraform plan -out=tfplan

# ==========================================
# 5. CONFIRMACIÓN
# ==========================================
echo ""
echo "=========================================="
echo "⚠️  REVISIÓN DE PLAN"
echo "=========================================="
echo ""
echo "Terraform creará los siguientes recursos:"
echo "  - 1 instancia EC2 (MongoDB)"
echo "  - 3 funciones Lambda"
echo "  - 1 Lambda Layer"
echo "  - 1 API Gateway REST API"
echo "  - Security Groups, IAM roles, CloudWatch logs"
echo ""
read -p "¿Deseas aplicar estos cambios? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "❌ Despliegue cancelado"
  exit 0
fi

# ==========================================
# 6. TERRAFORM APPLY
# ==========================================
echo ""
echo "5️⃣  Aplicando infraestructura..."
echo ""

terraform apply tfplan

# ==========================================
# 7. OUTPUTS
# ==========================================
echo ""
echo "=========================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""

terraform output

echo ""
echo "🔗 Endpoints disponibles:"
terraform output -json endpoints | jq -r 'to_entries[] | "   \(.key): \(.value)"'

echo ""
echo "📝 Próximos pasos:"
echo "   1. Espera ~3 minutos para que MongoDB se inicialice"
echo "   2. Ejecuta: ./scripts/test_endpoints.sh"
echo "   3. Revisa logs en CloudWatch"
