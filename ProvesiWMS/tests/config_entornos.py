"""
═══════════════════════════════════════════════════════════════════════════════
CONFIGURACIÓN DE ENTORNOS - PRUEBAS DE CARGA
═══════════════════════════════════════════════════════════════════════════════

Este archivo centraliza la configuración para todas las pruebas de carga.
Para cambiar de entorno (local → AWS → producción), solo edita las variables.

Variables configurables:
    BASE_URL    - URL base del servidor (con puerto si aplica)
    TIMEOUT     - Timeout para requests HTTP (segundos)
    HEADERS     - Headers HTTP adicionales (autenticación, etc.)
    
Puerto configurable:
    Cambia el puerto en BASE_URL directamente:
    - Local desarrollo: http://127.0.0.1:8000
    - Load balancer: http://your-lb.amazonaws.com:80
    - Custom port: http://your-lb.amazonaws.com:8080

Base de datos:
    - Desarrollo: SQLite (solo para tests no concurrentes)
    - Producción: PostgreSQL (requerido para concurrencia y thread-safety)
    
═══════════════════════════════════════════════════════════════════════════════
"""

import os

# =============================================================================
# DESARROLLO LOCAL
# =============================================================================
# Puerto configurable: cambiar 8000 por el que necesites
BASE_URL = os.environ.get('BASE_URL', "http://provesi-alb-135468775.us-east-1.elb.amazonaws.com/inventario/")
TIMEOUT = int(os.environ.get('TIMEOUT', '30'))  # segundos


# =============================================================================
# AWS - EJEMPLOS (Descomentar y actualizar según necesites)
# =============================================================================

# AWS Application Load Balancer - HTTP (puerto 80)
# BASE_URL = "http://your-alb-name-123456789.us-east-1.elb.amazonaws.com"
# TIMEOUT = 60

# AWS Application Load Balancer - HTTPS (puerto 443)
# BASE_URL = "https://your-alb-name-123456789.us-east-1.elb.amazonaws.com"
# TIMEOUT = 60

# AWS con puerto personalizado
# BASE_URL = "http://your-alb-name-123456789.us-east-1.elb.amazonaws.com:8080"
# TIMEOUT = 60

# Dominio personalizado (Route 53 + ALB + ACM)
# BASE_URL = "https://api.tudominio.com"
# TIMEOUT = 60

# Elastic Beanstalk
# BASE_URL = "http://your-env-name.us-east-1.elasticbeanstalk.com"
# TIMEOUT = 60


# =============================================================================
# PARÁMETROS DE PRUEBAS
# =============================================================================

# Workers para pruebas concurrentes (Django tests)
WORKERS_TEST_1000 = 10      # Test de 1,000 artículos
WORKERS_TEST_10000 = 50     # Test de 10,000 artículos

# Límites de tiempo
TIEMPO_MAX_10000 = 300      # 5 minutos para 10,000 artículos

# Requisitos de throughput
REQUISITO_REQ_MIN = 2000    # 2,000 req/min (objetivo máximo)

# Umbrales de éxito
UMBRAL_EXITO_PCT = 95       # 95% de artículos creados exitosamente
UMBRAL_ERROR_4XX = 5        # Máximo 5% de errores 4xx
UMBRAL_ERROR_5XX = 1        # Máximo 1% de errores 5xx


# =============================================================================
# AUTENTICACIÓN (Opcional)
# =============================================================================

# Sin autenticación (por defecto)
HEADERS = {
    "Content-Type": "application/json"
}

# Con API Key (descomentar si aplica):
# API_KEY = os.environ.get('API_KEY', 'your-api-key-here')
# HEADERS = {
#     "Content-Type": "application/json",
#     "x-api-key": API_KEY
# }

# Con Bearer Token JWT (descomentar si aplica):
# AUTH_TOKEN = os.environ.get('AUTH_TOKEN', 'your-jwt-token-here')
# HEADERS = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {AUTH_TOKEN}"
# }


# =============================================================================
# DOCUMENTACIÓN
# =============================================================================
"""
📖 GUÍAS COMPLETAS:

Para deployment en AWS:
    → Ver: tests/README_AWS_DEPLOYMENT.md
    
Para ejecutar pruebas:
    → Ver: tests/README_LOAD_TESTING.md

Para cambiar puerto:
    Edita BASE_URL:
    - Local: http://127.0.0.1:8000 (puerto 8000)
    - Load Balancer: http://your-lb.amazonaws.com:80 (puerto 80)
    - Custom: http://your-lb.amazonaws.com:8080 (puerto 8080)
    
Para cambiar a PostgreSQL (producción):
    1. Actualizar settings.py con credenciales PostgreSQL
    2. No es necesario cambiar este archivo
    3. Los tests funcionarán automáticamente
    
Variables de entorno (opcional):
    export BASE_URL="http://production-server.com"
    export TIMEOUT="60"
    export API_KEY="your-key"
"""

