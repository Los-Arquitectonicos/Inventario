#!/bin/bash

# Script de Ejecucion de Pruebas de Carga
# Valida escalabilidad: 100 → 2,000 req/min, 10,000 registros en <5 min
#
# Uso:
#   ./tests/run_load_tests.sh [modo]
#
# Modos:
#   all       - Ejecuta todas las pruebas (por defecto)
#   baseline  - Prueba baseline (100 req/min, 1 min)
#   medium    - Carga media (500 req/min, 2 min)
#   high      - Carga alta (1,000 req/min, 3 min)
#   max       - Carga maxima (2,000 req/min, 5 min)
#   objective - Prueba objetivo (10,000 articulos, 5 min)
#   web       - Interfaz web de Locust

set -e

# Configuracion
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$BASE_URL" ]; then
    BASE_URL=$(python -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from config_entornos import BASE_URL; print(BASE_URL)" 2>/dev/null || echo "http://127.0.0.1:8000")
fi

LOCUSTFILE="$SCRIPT_DIR/locustfile.py"
REPORTES_DIR="$SCRIPT_DIR/reportes"

mkdir -p "$REPORTES_DIR"
# Funciones auxiliares

print_header() {
    echo ""
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
    echo ""
}

print_info() {
    echo "[INFO] $1"
}

print_success() {
    echo "[OK] $1"
}

print_warning() {
    echo "[WARNING] $1"
}

print_error() {
    echo "[ERROR] $1"
}

check_dependencies() {
    print_info "Verificando dependencias..."
    
    if ! command -v python &> /dev/null; then
        print_error "Python no esta instalado"
        exit 1
    fi
    
    if ! python -c "import locust" 2>/dev/null; then
        print_warning "Locust no esta instalado"
        print_info "Instalando Locust..."
        pip install locust
        print_success "Locust instalado"
    fi
    
    if [ ! -f "$LOCUSTFILE" ]; then
        print_error "No se encuentra locustfile.py en: $LOCUSTFILE"
        exit 1
    fi
    
    print_info "Verificando servidor en $BASE_URL..."
    
    if [[ "$BASE_URL" == *"/inventario/"* ]]; then
        CHECK_URL="$BASE_URL"
    else
        CHECK_URL="${BASE_URL}/inventario/"
    fi
    
    if curl -s -f -m 10 "$CHECK_URL" > /dev/null 2>&1; then
        print_success "Servidor respondiendo"
    else
        print_warning "No se pudo verificar servidor en $CHECK_URL"
        print_info "Continuando (servidor puede estar remoto)"
    fi
}
run_test() {
    local test_name=$1
    local users=$2
    local spawn_rate=$3
    local run_time=$4
    local description=$5
    local expected_req_min=$6
    
    print_header "$test_name: $description"
    
    print_info "Configuracion:"
    echo "  Usuarios simultaneos: $users"
    echo "  Velocidad de inicio: $spawn_rate usuarios/seg"
    echo "  Duracion: $run_time"
    echo "  Throughput esperado: ~$expected_req_min req/min"
    echo "  Host: $BASE_URL"
    echo ""
    
    print_info "Ejecutando prueba..."
    
    # Pasar nombre del perfil como variable de entorno
    LOCUST_PROFILE="$test_name" locust -f "$LOCUSTFILE" \
        --host="$BASE_URL" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="$run_time" \
        --headless
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Prueba completada"
    else
        print_error "Prueba fallo con codigo $exit_code"
    fi
    
    echo ""
    sleep 2
}
# Definicion de pruebas

test_baseline() {
    run_test "baseline" 2 1 "1m" "Linea base" "100"
}

test_medium() {
    run_test "medium" 10 2 "2m" "Carga media" "500"
}

test_high() {
    run_test "high" 20 5 "3m" "Carga alta" "1000"
}

test_max() {
    run_test "max" 40 10 "5m" "Carga maxima" "2000"
}

test_objective() {
    run_test "objective" 35 7 "5m" "Objetivo 10k articulos" "~2000"
}

test_web() {
    print_header "INTERFAZ WEB DE LOCUST"
    print_info "Abriendo interfaz web..."
    print_info "Accede a: http://localhost:8089"
    print_warning "Presiona Ctrl+C para detener"
    echo ""
    
    locust -f "$LOCUSTFILE" --host="$BASE_URL"
}
# Funcion principal

main() {
    local mode=${1:-all}
    
    print_header "PRUEBAS DE CARGA - INVENTARIO WMS"
    
    echo "Requerimiento:"
    echo "  Escalar de 100 a 2,000 req/min"
    echo "  Procesar 10,000 registros en < 5 minutos"
    echo ""
    
    check_dependencies
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    echo ""
    print_info "Timestamp: $TIMESTAMP"
    
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
            echo "Modos validos:"
            echo "  all       - Todas las pruebas"
            echo "  baseline  - Linea base (100 req/min, 1 min)"
            echo "  medium    - Carga media (500 req/min, 2 min)"
            echo "  high      - Carga alta (1,000 req/min, 3 min)"
            echo "  max       - Carga maxima (2,000 req/min, 5 min)"
            echo "  objective - Objetivo (10,000 articulos, 5 min)"
            echo "  web       - Interfaz web"
            exit 1
            ;;
    esac
    
    if [ "$mode" != "web" ]; then
        print_header "RESUMEN"
        print_success "Pruebas completadas"
        print_info "Reportes JSON en: $REPORTES_DIR/"
        
        echo ""
        ls -1t "$REPORTES_DIR"/*.json 2>/dev/null | head -5 || echo "  (ninguno)"
        echo ""
    fi
    
    echo ""
}

main "$@"
