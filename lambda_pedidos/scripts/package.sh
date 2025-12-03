#!/bin/bash
# Script para empaquetar Lambda Layer y funciones

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "📦 EMPAQUETANDO LAMBDA PEDIDOS"
echo "=========================================="

# ==========================================
# 1. EMPAQUETAR LAMBDA LAYER
# ==========================================
echo ""
echo "1️⃣  Empaquetando Lambda Layer..."

cd "$PROJECT_ROOT/layer"

# Instalar dependencias en carpeta python/
pip3 install -r requirements.txt -t python/ --upgrade --quiet

# Crear ZIP del layer
if [ -f "$PROJECT_ROOT/layer.zip" ]; then
  rm "$PROJECT_ROOT/layer.zip"
fi

zip -r "$PROJECT_ROOT/layer.zip" python/ -x "*.pyc" -x "*__pycache__*"

echo "✅ Layer empaquetado: layer.zip ($(du -h "$PROJECT_ROOT/layer.zip" | cut -f1))"

# ==========================================
# 2. EMPAQUETAR FUNCIONES LAMBDA
# ==========================================
echo ""
echo "2️⃣  Empaquetando funciones Lambda..."

cd "$PROJECT_ROOT/functions"

for func in crear_pedido consultar_pedido seguir_pedido; do
  echo "   📄 Empaquetando $func..."
  
  # Eliminar ZIP anterior si existe
  if [ -f "$PROJECT_ROOT/functions/${func}.zip" ]; then
    rm "$PROJECT_ROOT/functions/${func}.zip"
  fi
  
  # Crear ZIP de la función
  zip "$PROJECT_ROOT/functions/${func}.zip" "${func}.py"
  
  echo "      ✅ ${func}.zip ($(du -h "$PROJECT_ROOT/functions/${func}.zip" | cut -f1))"
done

# ==========================================
# RESUMEN
# ==========================================
echo ""
echo "=========================================="
echo "✅ EMPAQUETADO COMPLETO"
echo "=========================================="
echo ""
echo "Archivos generados:"
echo "  - layer.zip"
echo "  - functions/crear_pedido.zip"
echo "  - functions/consultar_pedido.zip"
echo "  - functions/seguir_pedido.zip"
echo ""
echo "Siguiente paso: cd terraform && terraform init && terraform plan"
