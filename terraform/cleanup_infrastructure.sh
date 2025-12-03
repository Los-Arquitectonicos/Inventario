#!/bin/bash

# ================================================================
# SCRIPT DE LIMPIEZA Y RESET PARA AWS CLOUDSHELL
# ================================================================
# ProvesiWMS - Destruir y limpiar infraestructura
#
# Uso: ./cleanup_infrastructure.sh
#
# Este script:
# 1. Destruye toda la infraestructura existente
# 2. Limpia archivos de estado de Terraform
# 3. Prepara para un nuevo despliegue limpio
# ================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Verificar que estamos en el directorio correcto
check_terraform_directory() {
    if [[ ! -f "main.tf" ]]; then
        error "No se encontró main.tf. ¿Estás en el directorio terraform?"
        exit 1
    fi
}

# Destruir infraestructura
destroy_infrastructure() {
    log "Verificando si existe infraestructura desplegada..."
    
    if [[ -f "terraform.tfstate" ]] || [[ -f ".terraform/terraform.tfstate" ]]; then
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}  ADVERTENCIA: DESTRUCCIÓN TOTAL${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo "Esta operación DESTRUIRÁ PERMANENTEMENTE:"
        echo "• Todas las instancias EC2"
        echo "• La base de datos PostgreSQL (¡SE PERDERÁN TODOS LOS DATOS!)"
        echo "• El Application Load Balancer"
        echo "• Todos los grupos de seguridad"
        echo "• Todas las configuraciones de red"
        echo ""
        echo -e "${RED}ESTO NO SE PUEDE DESHACER${NC}"
        echo ""
        
        read -p "¿Estás ABSOLUTAMENTE SEGURO de que quieres continuar? (escribe 'DESTROY'): " confirm
        
        if [[ "$confirm" != "DESTROY" ]]; then
            log "Operación cancelada. Infraestructura preservada."
            exit 0
        fi
        
        log "Destruyendo infraestructura..."
        terraform destroy -auto-approve
        log "Infraestructura destruida"
    else
        warn "No se encontró infraestructura desplegada"
    fi
}

# Limpiar archivos de estado
cleanup_state() {
    log "Limpiando archivos de estado de Terraform..."
    
    # Hacer backup del estado si existe
    if [[ -f "terraform.tfstate" ]]; then
        cp terraform.tfstate "terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)"
        log "Backup del estado creado"
    fi
    
    # Eliminar archivos de estado
    rm -f terraform.tfstate*
    rm -f tfplan
    rm -rf .terraform/
    
    log "Archivos de estado eliminados"
}

# Verificar limpieza
verify_cleanup() {
    log "Verificando limpieza..."
    
    # Verificar que no queden recursos
    if command -v terraform &> /dev/null; then
        terraform init -backend=false
        
        # Intentar listar recursos (debería estar vacío)
        if terraform state list 2>/dev/null | grep -q .; then
            warn "Aún hay recursos en el estado. Ejecutar terraform destroy nuevamente."
        else
            log "✓ Estado de Terraform limpio"
        fi
    fi
    
    # Verificar archivos
    if [[ -f "terraform.tfstate" ]] || [[ -d ".terraform" ]]; then
        warn "Algunos archivos de estado aún existen"
    else
        log "✓ Archivos de estado eliminados"
    fi
}

# Preparar para nuevo despliegue
prepare_fresh_deployment() {
    log "Preparando para nuevo despliegue..."
    
    # Inicializar Terraform limpio
    if command -v terraform &> /dev/null; then
        terraform init
        log "Terraform reinicializado"
    fi
    
    # Verificar configuración
    if [[ -f "terraform.tfvars" ]]; then
        log "✓ Archivo terraform.tfvars encontrado"
    else
        if [[ -f "terraform.tfvars.example" ]]; then
            cp terraform.tfvars.example terraform.tfvars
            log "Archivo terraform.tfvars creado desde ejemplo"
        else
            warn "No se encontró terraform.tfvars. Créalo antes del despliegue."
        fi
    fi
}

# Mostrar información post-limpieza
show_post_cleanup_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  LIMPIEZA COMPLETADA${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    echo "El entorno está limpio y listo para un nuevo despliegue."
    echo ""
    echo "Para desplegar nuevamente:"
    echo "  ./deploy_complete_infrastructure.sh"
    echo ""
    echo "O manualmente:"
    echo "  terraform plan"
    echo "  terraform apply"
    echo ""
}

# Función principal
main() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  LIMPIEZA DE INFRAESTRUCTURA${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    
    check_terraform_directory
    destroy_infrastructure
    cleanup_state
    verify_cleanup
    prepare_fresh_deployment
    show_post_cleanup_info
    
    log "¡Limpieza completada exitosamente!"
}

# Manejar Ctrl+C
trap 'echo -e "\n${RED}Operación cancelada por el usuario${NC}"; exit 1' INT

# Ejecutar función principal
main "$@"