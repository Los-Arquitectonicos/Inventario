#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# Script de Ejecución de Pruebas de Carga
# ═══════════════════════════════════════════════════════════════════════════════
#
# Este script ejecuta todas las pruebas de carga del sistema de inventario
# validando el requerimiento de escalabilidad (100 → 2,000 req/min)
#
# Uso:
#   ./tests/run_load_tests.sh [modo]
#
# Modos:
#   all       - Ejecuta todas las pruebas (por defecto)
#   baseline  - Solo prueba baseline (100 req/min)
#   medium    - Solo prueba media carga (500 req/min)
#   high      - Solo prueba alta carga (1,000 req/min)
#   max       - Solo prueba máxima carga (2,000 req/min)
#   objective - Solo prueba objetivo (10,000 artículos)
#   web       - Abre interfaz web de Locust
#
# Ejemplos:
#   ./tests/run_load_tests.sh
#   ./tests/run_load_tests.sh baseline
#   ./tests/run_load_tests.sh web
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Leer configuración de tests/config_entornos.py
BASE_URL=${BASE_URL:-"http://127.0.0.1:8000"}
LOCUSTFILE="tests/locustfile.py"
REPORTES_DIR="tests/reportes"

# Crear directorio de reportes si no existe
mkdir -p "$REPORTES_DIR"

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    print_info "Verificando dependencias..."
    
    # Verificar Python
    if ! command -v python &> /dev/null; then
        print_error "Python no está instalado"
        exit 1
    fi
    
    # Verificar Locust
    if ! python -c "import locust" 2>/dev/null; then
        print_warning "Locust no está instalado"
        print_info "Instalando Locust..."
        pip install locust
        print_success "Locust instalado correctamente"
    fi
    
    # Verificar que el servidor esté corriendo
    print_info "Verificando servidor en $BASE_URL..."
    if curl -s -f "$BASE_URL/inventario/" > /dev/null 2>&1; then
        print_success "Servidor está corriendo"
    else
        print_error "Servidor no está corriendo en $BASE_URL"
        print_info "Por favor, inicia el servidor con: python manage.py runserver"
        exit 1
    fi
}

run_test() {
    local test_name=$1
    local users=$2
    local spawn_rate=$3
    local run_time=$4
    local description=$5
    
    print_header "$test_name: $description"
    
    print_info "Configuración:"
    echo "   • Usuarios: $users"
    echo "   • Spawn rate: $spawn_rate usuarios/seg"
    echo "   • Duración: $run_time"
    echo "   • Host: $BASE_URL"
    echo ""
    
    print_info "Iniciando prueba..."
    
    # Ejecutar Locust
    locust -f "$LOCUSTFILE" \
        --host="$BASE_URL" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="$run_time" \
        --headless \
        --html="$REPORTES_DIR/reporte_${test_name}.html" \
        --csv="$REPORTES_DIR/reporte_${test_name}"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Prueba completada"
    else
        print_error "Prueba falló con código $exit_code"
    fi
    
    echo ""
    sleep 2  # Pausa entre tests
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEFINICIÓN DE PRUEBAS
# ═══════════════════════════════════════════════════════════════════════════════

test_baseline() {
    run_test "baseline" 2 1 "1m" "100 req/min - Línea base"
}

test_medium() {
    run_test "medium" 10 2 "2m" "500 req/min - Carga media"
}

test_high() {
    run_test "high" 20 5 "3m" "1,000 req/min - Carga alta"
}

test_max() {
    run_test "max" 40 10 "5m" "2,000 req/min - Carga máxima"
}

test_objective() {
    run_test "objective" 35 7 "5m" "10,000 artículos - Prueba objetivo"
}

test_web() {
    print_header "INTERFAZ WEB DE LOCUST"
    print_info "Abriendo interfaz web..."
    print_info "Accede a: http://localhost:8089"
    print_warning "Presiona Ctrl+C para detener"
    echo ""
    
    locust -f "$LOCUSTFILE" --host="$BASE_URL"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    local mode=${1:-all}
    
    print_header "🚀 PRUEBAS DE CARGA - INVENTARIO WMS"
    
    echo -e "${CYAN}Requerimiento:${NC}"
    echo "  Escalar de 100 req/min a 2,000 req/min"
    echo "  Procesar 10,000 registros en < 5 minutos"
    echo ""
    
    # Verificar dependencias
    check_dependencies
    
    # Timestamp para reportes
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    echo ""
    print_info "Timestamp de ejecución: $TIMESTAMP"
    
    # Ejecutar pruebas según el modo
    case $mode in
        all)
            print_info "Ejecutando TODAS las pruebas..."
            test_baseline
            test_medium
            test_high
            test_max
            test_objective
            ;;
        baseline)
            test_baseline
            ;;
        medium)
            test_medium
            ;;
        high)
            test_high
            ;;
        max)
            test_max
            ;;
        objective)
            test_objective
            ;;
        web)
            test_web
            ;;
        *)
            print_error "Modo desconocido: $mode"
            echo ""
            echo "Modos válidos:"
            echo "  all       - Todas las pruebas (por defecto)"
            echo "  baseline  - Prueba baseline (100 req/min)"
            echo "  medium    - Carga media (500 req/min)"
            echo "  high      - Carga alta (1,000 req/min)"
            echo "  max       - Carga máxima (2,000 req/min)"
            echo "  objective - Prueba objetivo (10,000 artículos)"
            echo "  web       - Interfaz web"
            exit 1
            ;;
    esac
    
    # Resumen final
    if [ "$mode" != "web" ]; then
        print_header "📊 RESUMEN FINAL"
        print_success "Pruebas completadas"
        print_info "Reportes guardados en: $REPORTES_DIR/"
        
        # Listar reportes generados
        echo ""
        echo "Reportes HTML:"
        ls -1 "$REPORTES_DIR"/*.html 2>/dev/null | tail -5 || echo "  (ninguno)"
        
        echo ""
        echo "Reportes JSON:"
        ls -1 tests/reporte_locust_*.json 2>/dev/null | tail -5 || echo "  (ninguno)"
        
        echo ""
        print_info "Para ver reportes HTML, abre en tu navegador:"
        echo "  file://$(pwd)/$REPORTES_DIR/reporte_<nombre>.html"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# EJECUTAR
# ═══════════════════════════════════════════════════════════════════════════════

main "$@"
