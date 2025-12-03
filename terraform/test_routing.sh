#!/bin/bash

# ================================================================
# SCRIPT DE TESTING DE ROUTING KONG API GATEWAY
# ================================================================
# Prueba el routing entre ALB → Kong → Backend Services
#
# Uso: ./test_routing.sh [ALB_DNS]
# Ejemplo: ./test_routing.sh provesi-alb-123456789.us-east-1.elb.amazonaws.com
# ================================================================

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
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

# Función para probar endpoint
test_endpoint() {
    local url="$1"
    local description="$2"
    local expected_status="${3:-200}"
    
    echo ""
    info "Testing: $description"
    info "URL: $url"
    
    # Hacer request con timeout
    if response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time 10 "$url" 2>/dev/null); then
        http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        body=$(echo "$response" | sed -e 's/HTTPSTATUS\:.*//g')
        
        if [[ "$http_code" == "$expected_status" ]]; then
            log "✅ SUCCESS - Status: $http_code"
            
            # Intentar parsear JSON
            if echo "$body" | python3 -m json.tool >/dev/null 2>&1; then
                echo "$body" | python3 -m json.tool | head -10
            else
                echo "$body" | head -5
            fi
        else
            error "❌ FAILED - Expected: $expected_status, Got: $http_code"
            echo "$body" | head -5
        fi
    else
        error "❌ FAILED - Connection error or timeout"
    fi
}

# Función principal de testing
run_tests() {
    local alb_dns="$1"
    
    if [[ -z "$alb_dns" ]]; then
        error "ALB DNS name is required"
        echo "Usage: $0 <ALB_DNS_NAME>"
        echo "Example: $0 provesi-alb-123456789.us-east-1.elb.amazonaws.com"
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  KONG API GATEWAY ROUTING TESTS${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Testing routing through ALB → Kong → Backend Services"
    echo "ALB DNS: $alb_dns"
    echo ""
    
    # Test 1: ALB Health Check
    test_endpoint "http://$alb_dns" "ALB Root - Should route through Kong"
    
    # Test 2: Notifications Service Routes (direct to notifications)
    test_endpoint "http://$alb_dns/notifications" "Notifications Root - Should route to notifications service"
    test_endpoint "http://$alb_dns/notifications/health" "Notifications Health - Should route to notifications service"
    test_endpoint "http://$alb_dns/notifications/test" "Notifications Test - Should route to notifications service"
    
    # Test 3: Django API Routes (to load balancer)
    test_endpoint "http://$alb_dns/inventario" "Django API Root - Should route to Django through ALB" 404
    test_endpoint "http://$alb_dns/api" "Django API - Should route to Django through ALB" 404
    test_endpoint "http://$alb_dns/admin" "Django Admin - Should route to Django through ALB" 404
    
    # Test 4: Non-existent routes
    test_endpoint "http://$alb_dns/nonexistent" "Non-existent Route - Should return 404" 404
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  TESTING COMPLETED${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    echo -e "${YELLOW}Expected Results:${NC}"
    echo "✅ /notifications/* → Notifications Service (simplified)"
    echo "❌ /inventario/* → Django API (not deployed yet, will show 404)"
    echo "❌ /api/* → Django API (not deployed yet, will show 404)"
    echo "❌ /admin/* → Django Admin (not deployed yet, will show 404)"
    echo ""
    
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. If notifications routes work → Kong routing is configured correctly"
    echo "2. Django routes will work once Django services are deployed"
    echo "3. All 404s for Django routes are expected until full deployment"
    echo ""
}

# Función para testing con terraform outputs
test_with_terraform() {
    info "Getting ALB DNS from Terraform outputs..."
    
    if ! command -v terraform &> /dev/null; then
        error "Terraform not found. Install it or provide ALB DNS manually."
        exit 1
    fi
    
    if [[ ! -f "main.tf" ]]; then
        error "Not in terraform directory. Run from terraform/ folder."
        exit 1
    fi
    
    # Obtener ALB DNS de terraform
    if alb_dns=$(terraform output -raw application_load_balancer_dns 2>/dev/null); then
        info "Found ALB DNS: $alb_dns"
        run_tests "$alb_dns"
    else
        error "Could not get ALB DNS from terraform. Infrastructure might not be deployed."
        echo ""
        echo "Deploy infrastructure first:"
        echo "  ./deploy_complete_infrastructure.sh"
        echo ""
        echo "Or provide ALB DNS manually:"
        echo "  $0 your-alb-dns-name.amazonaws.com"
        exit 1
    fi
}

# Script principal
main() {
    if [[ $# -eq 0 ]]; then
        # No arguments - try to get from terraform
        test_with_terraform
    else
        # ALB DNS provided as argument
        run_tests "$1"
    fi
}

# Ejecutar función principal
main "$@"