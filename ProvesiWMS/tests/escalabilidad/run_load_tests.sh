#!/bin/bash

# Script de Ejecucion de Pruebas de Carga
# Valida escalabilidad: 100 → 2,000 req/min, 10,000 registros en <5 min
#
# ============================================================================
# METODOLOGÍA DE CÁLCULO DE USUARIOS Y SPAWN RATE
# ============================================================================
#
# 1. CÁLCULO DE USUARIOS
#    Formula base: usuarios = throughput_objetivo / capacidad_por_usuario
#    
#    Donde:
#    - throughput_objetivo: req/min que se desea alcanzar (del ASR)
#    - capacidad_por_usuario: ~50 req/min (basado en wait_time de 0.3s)
#    
#    Ejemplo para 1,000 req/min:
#      usuarios = 1,000 / 50 = 20 usuarios
#
# 2. CÁLCULO DE SPAWN RATE
#    Formula heurística: spawn_rate = usuarios / factor
#    
#    Donde:
#    - factor: 2-5 (menor = rampa más lenta y controlada)
#    - objetivo: tiempo_rampa < 10% de duración_total
#    
#    Ejemplo para 20 usuarios:
#      spawn_rate = 20 / 4 = 5 usuarios/seg
#      tiempo_rampa = 20 / 5 = 4 segundos
#
# 3. SELECCIÓN DE DURACIÓN
#    Principios:
#    - Mínimo: 1 minuto (permite estabilización)
#    - Máximo: 5 minutos (límite ASR: "10,000 en < 5 min")
#    - Progresión: más tiempo para cargas más altas (detecta degradación)
#
# 4. ESCALAMIENTO DE PERFILES
#    Usuarios:  2 → 10 (5x) → 20 (2x) → 40 (2x) → 35 (objetivo óptimo)
#    Spawn:     1 → 2       → 5       → 10      → 7
#    Duración:  1m → 2m     → 3m      → 5m      → 5m
#    Throughput: 100 → 500 → 1,000 → 2,000 → ~2,000 req/min
#
# 5. LIMITACIÓN DEL SISTEMA
#    Capacidad máxima: 2 servidores × 1,000 req/min ≈ 2,000 req/min
#    Más de 40 usuarios causaría saturación sin beneficio analítico
#
# ============================================================================
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
    # BASELINE - Línea Base Mínima
    # 
    # Objetivo: Validar funcionamiento básico con concurrencia mínima
    # 
    # Cálculo de usuarios:
    #   - Requisito: ~100 req/min (mínimo ASR)
    #   - Capacidad por usuario: ~50 req/min (con wait_time 0.3s)
    #   - Usuarios necesarios: 100 / 50 = 2 usuarios
    # 
    # Spawn rate:
    #   - Fórmula: usuarios / 2 = 2 / 2 = 1 usuario/seg
    #   - Tiempo de rampa: 2s (3% de 60s total)
    #   - Justificación: Inicio controlado para mediciones limpias
    # 
    # Duración:
    #   - 1 minuto = suficiente para ~100 requests
    #   - Permite validación rápida sin degradación
    # 
    # Throughput esperado: 2 usuarios × 50 req/min = 100 req/min
    run_test "baseline" 2 1 "1m" "Linea base" "100"
}

test_medium() {
    # MEDIUM - Carga Media
    # 
    # Objetivo: Validar escalamiento gradual (5x baseline)
    # 
    # Cálculo de usuarios:
    #   - Requisito: ~500 req/min (50% del rango ASR)
    #   - Capacidad por usuario: ~50 req/min
    #   - Usuarios necesarios: 500 / 50 = 10 usuarios
    # 
    # Spawn rate:
    #   - Fórmula: usuarios / 5 = 10 / 5 = 2 usuarios/seg
    #   - Tiempo de rampa: 5s (4% de 120s total)
    #   - Justificación: Balance entre rapidez y estabilidad
    # 
    # Duración:
    #   - 2 minutos = ~1,000 requests totales
    #   - Detecta degradación temprana (memory leaks, conexiones)
    # 
    # Throughput esperado: 10 usuarios × 50 req/min = 500 req/min
    run_test "medium" 10 2 "2m" "Carga media" "500"
}

test_high() {
    # HIGH - Carga Alta
    # 
    # Objetivo: Validar punto medio del rango ASR (50% de capacidad máxima)
    # 
    # Cálculo de usuarios:
    #   - Requisito: ~1,000 req/min (50% del máximo 2,000)
    #   - Capacidad por usuario: ~50 req/min
    #   - Usuarios necesarios: 1,000 / 50 = 20 usuarios
    # 
    # Spawn rate:
    #   - Fórmula: usuarios / 4 = 20 / 4 = 5 usuarios/seg
    #   - Tiempo de rampa: 4s (2% de 180s total)
    #   - Justificación: Rampa más agresiva para simular pico de carga
    # 
    # Duración:
    #   - 3 minutos = ~3,000 requests totales
    #   - Valida sostenibilidad bajo carga alta
    #   - Detecta saturación de connection pools
    # 
    # Throughput esperado: 20 usuarios × 50 req/min = 1,000 req/min
    # 
    # Nota: Suficiente para saturar 1 servidor EC2, pero NO 2 con ALB
    run_test "high" 20 5 "3m" "Carga alta" "1000"
}

test_max() {
    # MAX - Carga Máxima
    # 
    # Objetivo: Validar límite superior del ASR (capacidad máxima sostenible)
    # 
    # Cálculo de usuarios:
    #   - Requisito: ~2,000 req/min (máximo ASR)
    #   - Capacidad por usuario: ~50 req/min
    #   - Usuarios necesarios: 2,000 / 50 = 40 usuarios
    # 
    # Spawn rate:
    #   - Fórmula: usuarios / 4 = 40 / 4 = 10 usuarios/seg
    #   - Tiempo de rampa: 4s (1.3% de 300s total)
    #   - Justificación: Rampa máxima para simular pico súbito
    # 
    # Duración:
    #   - 5 minutos = ~10,000 requests totales
    #   - Valida sostenibilidad bajo máxima carga (requisito ASR)
    #   - Detecta memory leaks y connection exhaustion
    # 
    # Throughput esperado: 40 usuarios × 50 req/min = 2,000 req/min
    # 
    # Limitación del sistema:
    #   2 servidores EC2 × ~1,000 req/min/servidor = ~2,000 req/min máximo
    #   Más usuarios causaría saturación (timeouts, errores)
    run_test "max" 40 10 "5m" "Carga maxima" "2000"
}

test_objective() {
    # OBJECTIVE - Prueba de Aceptación del ASR
    # 
    # Objetivo: Validar requisito crítico "10,000 artículos en < 5 minutos"
    # 
    # Cálculo de usuarios:
    #   - Requisito: 10,000 artículos / 300 segundos = 33.33 artículos/seg
    #   - Throughput necesario: ~2,000 req/min (incluye GET, POST, validaciones)
    #   - Capacidad por usuario: ~57 req/min (optimizado para creación)
    #   - Usuarios necesarios: 2,000 / 57 ≈ 35 usuarios
    # 
    # ¿Por qué 35 y no 40 (max)?
    #   - Objetivo busca EFICIENCIA ÓPTIMA, no capacidad máxima
    #   - 30 usuarios → ~1,700 req/min (insuficiente para 10k en 5min)
    #   - 40 usuarios → ~2,200 req/min (excede y degrada estabilidad)
    #   - 35 usuarios → ~2,000 req/min (punto óptimo validado empíricamente)
    # 
    # Spawn rate:
    #   - Fórmula: usuarios / 5 = 35 / 5 = 7 usuarios/seg
    #   - Tiempo de rampa: 5s (1.7% de 300s total)
    #   - Justificación: Similar a max pero más controlado
    # 
    # Duración:
    #   - 5 minutos EXACTOS (requisito ASR no negociable)
    #   - No puede ser más corto (no validaría ASR)
    #   - No debe ser más largo (ASR especifica < 5 min)
    # 
    # Throughput esperado: 35 usuarios × 57 req/min ≈ 2,000 req/min
    # 
    # Validación de éxito:
    #   articulos_por_segundo = exitosos / 300
    #   cumple_ASR = (articulos_por_segundo >= 33.33) AND (tasa_exito >= 95%)
    # 
    # Margen de seguridad:
    #   - 5 usuarios menos que max (40) = 12.5% de margen
    #   - Permite mantener estabilidad durante 5 minutos completos
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
        print_info "Reportes en: $REPORTES_DIR/"
        
        echo ""
        echo "Reportes HTML:"
        ls -1 "$REPORTES_DIR"/*.html 2>/dev/null | tail -5 || echo "  (ninguno)"
        
        echo ""
        echo "Reportes JSON:"
        ls -1 "$SCRIPT_DIR"/reporte_locust_*.json 2>/dev/null | tail -5 || echo "  (ninguno)"
        
        echo ""
    fi
    
    echo ""
}

main "$@"
