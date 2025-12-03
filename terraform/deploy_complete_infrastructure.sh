#!/bin/bash

# ================================================================
# SCRIPT DE DESPLIEGUE AUTOMATIZADO PARA AWS CLOUDSHELL
# ================================================================
# ProvesiWMS - Despliegue completo de infraestructura
#
# Uso: ./deploy_complete_infrastructure.sh
#
# Este script automatiza:
# 1. Instalación de Terraform
# 2. Configuración del proyecto
# 3. Despliegue de toda la infraestructura
# 4. Verificaciones de conectividad
# ================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar que estamos en CloudShell
check_cloudshell() {
    if [[ ! "$AWS_EXECUTION_ENV" == "CloudShell"* ]]; then
        warn "Este script está optimizado para AWS CloudShell"
        warn "Verifica que tengas las credenciales AWS configuradas"
    fi
}

# Instalar Terraform si no existe
install_terraform() {
    if ! command -v terraform &> /dev/null; then
        log "Instalando Terraform..."
        
        # Detectar arquitectura
        ARCH=$(uname -m)
        if [[ "$ARCH" == "x86_64" ]]; then
            ARCH="amd64"
        elif [[ "$ARCH" == "aarch64" ]]; then
            ARCH="arm64"
        fi
        
        # Descargar e instalar
        TERRAFORM_VERSION="1.6.6"
        wget -q "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip"
        unzip -q terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip
        sudo mv terraform /usr/local/bin/
        rm terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip
        
        # Verificar instalación
        terraform version
        log "Terraform instalado correctamente"
    else
        info "Terraform ya está instalado: $(terraform version)"
    fi
}

# Configurar el proyecto
setup_project() {
    log "Configurando el proyecto..."
    
    # Verificar que estamos en el directorio correcto
    if [[ ! -f "main.tf" ]]; then
        error "No se encontró main.tf. ¿Estás en el directorio terraform?"
        exit 1
    fi
    
    # Crear terraform.tfvars si no existe
    if [[ ! -f "terraform.tfvars" ]]; then
        if [[ -f "terraform.tfvars.example" ]]; then
            cp terraform.tfvars.example terraform.tfvars
            log "Archivo terraform.tfvars creado desde el ejemplo"
        else
            warn "No se encontró terraform.tfvars ni terraform.tfvars.example"
        fi
    fi
    
    # Mostrar configuración actual
    info "Configuración actual en terraform.tfvars:"
    if [[ -f "terraform.tfvars" ]]; then
        grep -E "^[^#]" terraform.tfvars | head -10
    fi
}

# Desplegar infraestructura
deploy_infrastructure() {
    log "Iniciando despliegue de infraestructura..."
    
    # Inicializar Terraform
    log "Inicializando Terraform..."
    terraform init
    
    # Validar configuración
    log "Validando configuración..."
    terraform validate
    
    # Mostrar plan
    log "Generando plan de despliegue..."
    terraform plan -out=tfplan
    
    # Confirmar despliegue
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  CONFIRMACIÓN DE DESPLIEGUE${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "La infraestructura que se va a crear incluye:"
    echo "• Application Load Balancer"
    echo "• Django API (2 instancias)"
    echo "• Base de datos PostgreSQL (RDS)"
    echo "• Grupos de seguridad y networking"
    echo ""
    echo ""
    read -p "¿Deseas continuar con el despliegue? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        info "Despliegue cancelado por el usuario"
        exit 0
    fi
    
    # Aplicar infraestructura
    log "Desplegando infraestructura... (esto puede tomar 10-15 minutos)"
    terraform apply tfplan
    
    log "¡Infraestructura desplegada exitosamente!"
}

# Verificar el despliegue
verify_deployment() {
    log "Verificando el despliegue..."
    
    # Obtener outputs
    echo ""
    info "=== INFORMACIÓN DE LA INFRAESTRUCTURA ==="
    terraform output
    
 
    
    if terraform output application_load_balancer_dns &>/dev/null; then
        ALB_DNS=$(terraform output -raw application_load_balancer_dns)
        info "ALB DNS: $ALB_DNS"
    fi
    
    # Esperar a que los servicios estén listos
    log "Esperando a que los servicios estén listos..."
    sleep 30
    
    
    # Probar ALB
    if [[ -n "$ALB_DNS" ]]; then
        log "Probando Application Load Balancer..."
        if curl -f -s "http://$ALB_DNS" >/dev/null; then
            log "✓ ALB está respondiendo"
        else
            warn "ALB no está respondiendo aún (esto es normal, puede tomar unos minutos más)"
        fi
    fi
}

# Mostrar información post-despliegue
show_post_deployment_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  DESPLIEGUE COMPLETADO${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    if [[ -n "$ALB_DNS" ]]; then
        echo -e "${BLUE}URLs principales:${NC}"
        echo "• API Principal: http://$ALB_DNS/api/"
        echo "• Notifications: http://$ALB_DNS/notifications/"
        echo "• Django Admin: http://$ALB_DNS/admin/"
        echo ""
    fi
    
    if [[ -n "$KONG_IP" ]]; then
        echo -e "${BLUE}Kong API Gateway:${NC}"
        echo "• Admin API: http://$KONG_IP:8001/"
        echo "• Gateway: http://$KONG_IP:8000/"
        echo ""
    fi
    
    echo -e "${BLUE}Próximos pasos:${NC}"
    echo "1. Esperar 5-10 minutos para que todos los servicios estén completamente listos"
    echo "2. Probar las APIs usando curl o Postman"
    echo "3. Configurar SSL/TLS para producción"
    echo "4. Configurar monitoreo y alertas"
    echo ""
    
    echo -e "${YELLOW}Comandos útiles:${NC}"
    echo "• Ver estado: terraform state list"
    echo "• Ver outputs: terraform output"
    echo "• Destruir todo: terraform destroy"
    echo ""
    
    echo -e "${RED}IMPORTANTE:${NC}"
    echo "• Recuerda apagar la infraestructura cuando no la uses: terraform destroy"
    echo "• Monitorea los costos en la consola de AWS"
    echo ""
}

# Función principal
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  PROVESI WMS - DESPLIEGUE AWS${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_cloudshell
    install_terraform
    setup_project
    deploy_infrastructure
    verify_deployment
    show_post_deployment_info
    
    log "¡Script completado exitosamente!"
}

# Ejecutar función principal
main "$@"