#!/bin/bash

# Script de deployment rápido
# Ejecuta los comandos de Terraform en secuencia

set -e  # Salir si hay error

echo "========================================="
echo "Deployment de ProvesiWMS en AWS"
echo "========================================="
echo ""

# Verificar que Terraform esté instalado
if ! command -v terraform &> /dev/null; then
    echo "ERROR: Terraform no está instalado"
    echo "Instala desde: https://www.terraform.io/downloads"
    exit 1
fi

# Verificar que AWS CLI esté configurado
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS CLI no está configurado"
    echo "Ejecuta: aws configure"
    exit 1
fi

echo "1. Inicializando Terraform..."
terraform init

echo ""
echo "2. Validando configuración..."
terraform validate

echo ""
echo "3. Formateando archivos..."
terraform fmt

echo ""
echo "4. Generando plan de ejecución..."
terraform plan -out=tfplan

echo ""
echo "========================================="
echo "Plan generado exitosamente"
echo "========================================="
echo ""
echo "Revisa el plan anterior."
echo "Para aplicar los cambios, ejecuta:"
echo ""
echo "  terraform apply tfplan"
echo ""
echo "Para destruir todo, ejecuta:"
echo ""
echo "  terraform destroy"
echo ""
