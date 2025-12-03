#!/bin/bash
# Script para probar los endpoints del API Gateway

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

echo "=========================================="
echo "🧪 PROBANDO ENDPOINTS DE PEDIDOS"
echo "=========================================="

# ==========================================
# 1. OBTENER URL DEL API GATEWAY
# ==========================================
echo ""
echo "1️⃣  Obteniendo URL del API Gateway..."

cd "$TERRAFORM_DIR"

if [ ! -f "terraform.tfstate" ]; then
  echo "❌ Error: terraform.tfstate no existe"
  echo "   Ejecuta primero: ./scripts/deploy.sh"
  exit 1
fi

API_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")

if [ -z "$API_URL" ]; then
  echo "❌ Error: No se pudo obtener la URL del API Gateway"
  exit 1
fi

echo "   ✅ API URL: $API_URL"

# ==========================================
# 2. VARIABLES DE PRUEBA
# ==========================================

# IDs de ejemplo (ajustar según tu base de datos ProvesiWMS)
CLIENTE_ID=1
PRODUCTO_ID_1=1
PRODUCTO_ID_2=2

# ==========================================
# 3. CREAR PEDIDO
# ==========================================
echo ""
echo "2️⃣  Probando POST /pedidos (crear pedido)..."

PAYLOAD=$(cat <<EOF
{
  "cliente_id": $CLIENTE_ID,
  "productos": [
    {
      "producto_id": $PRODUCTO_ID_1,
      "cantidad": 10
    },
    {
      "producto_id": $PRODUCTO_ID_2,
      "cantidad": 5
    }
  ]
}
EOF
)

echo "   📤 Request:"
echo "$PAYLOAD" | jq .

RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo ""
echo "   📥 Response:"
echo "$RESPONSE" | jq .

# Extraer número de pedido
NUMERO_PEDIDO=$(echo "$RESPONSE" | jq -r '.numero_pedido' 2>/dev/null || echo "")

if [ -z "$NUMERO_PEDIDO" ] || [ "$NUMERO_PEDIDO" = "null" ]; then
  echo "   ❌ Error: No se pudo crear el pedido"
  exit 1
fi

echo ""
echo "   ✅ Pedido creado: $NUMERO_PEDIDO"

# ==========================================
# 4. CONSULTAR PEDIDO
# ==========================================
echo ""
echo "3️⃣  Probando GET /pedidos/$NUMERO_PEDIDO (consultar pedido)..."

RESPONSE=$(curl -s -X GET "$API_URL/$NUMERO_PEDIDO")

echo "   📥 Response:"
echo "$RESPONSE" | jq .

# ==========================================
# 5. LISTAR PEDIDOS
# ==========================================
echo ""
echo "4️⃣  Probando GET /pedidos (listar pedidos)..."

RESPONSE=$(curl -s -X GET "$API_URL?cliente_id=$CLIENTE_ID&limit=5")

echo "   📥 Response:"
echo "$RESPONSE" | jq .

# ==========================================
# 6. ACTUALIZAR ESTADO (confirmado)
# ==========================================
echo ""
echo "5️⃣  Probando PUT /pedidos/$NUMERO_PEDIDO/seguimiento (estado: confirmado)..."

PAYLOAD=$(cat <<EOF
{
  "nuevo_estado": "confirmado"
}
EOF
)

echo "   📤 Request:"
echo "$PAYLOAD" | jq .

RESPONSE=$(curl -s -X PUT "$API_URL/$NUMERO_PEDIDO/seguimiento" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo ""
echo "   📥 Response:"
echo "$RESPONSE" | jq .

# ==========================================
# 7. ACTUALIZAR ESTADO (en_preparacion)
# ==========================================
echo ""
echo "6️⃣  Probando PUT /pedidos/$NUMERO_PEDIDO/seguimiento (estado: en_preparacion)..."

PAYLOAD=$(cat <<EOF
{
  "nuevo_estado": "en_preparacion"
}
EOF
)

RESPONSE=$(curl -s -X PUT "$API_URL/$NUMERO_PEDIDO/seguimiento" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "   📥 Response:"
echo "$RESPONSE" | jq .

# ==========================================
# 8. INTENTAR TRANSICIÓN INVÁLIDA
# ==========================================
echo ""
echo "7️⃣  Probando transición inválida (en_preparacion -> entregado)..."

PAYLOAD=$(cat <<EOF
{
  "nuevo_estado": "entregado"
}
EOF
)

RESPONSE=$(curl -s -X PUT "$API_URL/$NUMERO_PEDIDO/seguimiento" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "   📥 Response (debe fallar):"
echo "$RESPONSE" | jq .

# ==========================================
# RESUMEN
# ==========================================
echo ""
echo "=========================================="
echo "✅ PRUEBAS COMPLETADAS"
echo "=========================================="
echo ""
echo "Pedido de prueba: $NUMERO_PEDIDO"
echo "Estado final: en_preparacion"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Revisa logs en CloudWatch: aws logs tail /aws/lambda/pedidos-crear --follow"
echo "   2. Conéctate a MongoDB: ssh -i key.pem ubuntu@\$(terraform output -raw mongodb_public_ip)"
echo "   3. Consulta pedidos: mongosh pedidos_db --eval 'db.orders.find().pretty()'"
