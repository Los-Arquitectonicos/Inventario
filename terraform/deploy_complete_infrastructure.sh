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
    
    # Obtener IPs y DNS
    if terraform output kong_public_ip &>/dev/null; then
        KONG_IP=$(terraform output -raw kong_public_ip)
        info "Kong IP: $KONG_IP"
    fi
    
    if terraform output alb_dns_name &>/dev/null; then
        ALB_DNS=$(terraform output -raw alb_dns_name)
        info "ALB DNS: $ALB_DNS"
    fi
    
    if terraform output notifications_public_ip &>/dev/null; then
        NOTIFICATIONS_IP=$(terraform output -raw notifications_public_ip)
        info "Notifications IP: $NOTIFICATIONS_IP"
    fi
    
    # Esperar a que los servicios estén listos
    log "Esperando a que los servicios se inicien automáticamente (esto toma ~3 minutos)..."
    sleep 180
    
    # Probar Kong
    if [[ -n "$KONG_IP" ]]; then
        log "Probando Kong API Gateway..."
        if curl -f -s -k "https://$KONG_IP:8443/notifications/health" >/dev/null; then
            log "✓ Kong está respondiendo"
        else
            warn "Kong no está respondiendo aún (puede tomar unos minutos más)"
        fi
    fi
    
    # Probar ALB
    if [[ -n "$ALB_DNS" ]]; then
        log "Probando Application Load Balancer..."
        if curl -f -s -k "https://$ALB_DNS/inventario/" >/dev/null; then
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
    echo -e "${GREEN}  DESPLIEGUE COMPLETADO - TODO AUTOMÁTICO${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    echo -e "${BLUE}✅ SERVICIOS INICIADOS AUTOMÁTICAMENTE:${NC}"
    echo ""
    
    if [[ -n "$KONG_IP" ]]; then
        echo -e "${BLUE}🚪 Kong API Gateway:${NC}"
        echo "  • HTTP:  http://$KONG_IP:8000"
        echo "  • HTTPS: https://$KONG_IP:8443"
        echo ""
    fi
    
    if [[ -n "$ALB_DNS" ]]; then
        echo -e "${BLUE}🔗 Endpoints principales (a través de Kong):${NC}"
        echo "  • Django API:     https://$KONG_IP:8443/inventario/"
        echo "  • Django Admin:   https://$KONG_IP:8443/admin/"
        echo "  • Notifications:  https://$KONG_IP:8443/notifications/health"
        echo ""
        echo -e "${BLUE}📊 Load Balancer directo:${NC}"
        echo "  • ALB HTTPS: https://$ALB_DNS/inventario/"
        echo ""
    fi
    
    if [[ -n "$NOTIFICATIONS_IP" ]]; then
        echo -e "${BLUE}📬 Notifications Service:${NC}"
        echo "  • Direct: http://$NOTIFICATIONS_IP:8001/health"
        echo ""
    fi
    
    echo -e "${YELLOW}🧪 COMANDOS DE PRUEBA:${NC}"
    echo ""
    if [[ -n "$KONG_IP" ]]; then
        echo "# Probar Django a través de Kong"
        echo "curl -k https://$KONG_IP:8443/inventario/"
        echo ""
        echo "# Probar Notifications a través de Kong"
        echo "curl -k https://$KONG_IP:8443/notifications/health"
        echo ""
        echo "# Login en Notifications"
        echo "curl -k -X POST https://$KONG_IP:8443/notifications/auth/login \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
        echo ""
    fi
    
    echo -e "${BLUE}📋 INFORMACIÓN ÚTIL:${NC}"
    echo "  • Ver estado completo: terraform output"
    echo "  • Ver logs Django: ssh ubuntu@<DJANGO_IP> 'tail -f /home/ubuntu/django.log'"
    echo "  • Ver logs Notifications: ssh ubuntu@$NOTIFICATIONS_IP 'tail -f /home/ubuntu/notifications.log'"
    echo ""
    
    echo -e "${RED}⚠️  IMPORTANTE:${NC}"
    echo "  • Los servicios tardan ~3 minutos en estar completamente operativos"
    echo "  • Apaga la infraestructura cuando no la uses: terraform destroy"
    echo "  • Monitorea los costos en AWS Console"
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