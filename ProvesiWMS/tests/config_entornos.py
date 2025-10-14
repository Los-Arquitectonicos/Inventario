"""
Configuración de URLs para pruebas de carga en diferentes entornos
===================================================================

Este archivo centraliza las URLs para facilitar el cambio entre entornos.
Simplemente descomenta la configuración que necesites.
"""

# =============================================================================
# DESARROLLO LOCAL
# =============================================================================
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30  # segundos


# =============================================================================
# AWS APPLICATION LOAD BALANCER (ALB) - HTTP
# =============================================================================
# BASE_URL = "http://your-alb-name-123456789.us-east-1.elb.amazonaws.com"
# TIMEOUT = 60  # Mayor timeout para redes remotas


# =============================================================================
# AWS APPLICATION LOAD BALANCER (ALB) - HTTPS con certificado
# =============================================================================
# BASE_URL = "https://your-alb-name-123456789.us-east-1.elb.amazonaws.com"
# TIMEOUT = 60


# =============================================================================
# DOMINIO PERSONALIZADO (Route 53 + ALB + ACM)
# =============================================================================
# BASE_URL = "https://api.tudominio.com"
# TIMEOUT = 60


# =============================================================================
# AWS ELASTIC BEANSTALK
# =============================================================================
# BASE_URL = "http://your-env-name.us-east-1.elasticbeanstalk.com"
# TIMEOUT = 60


# =============================================================================
# CONFIGURACIÓN DE PRUEBAS DE CARGA
# =============================================================================

# Workers para pruebas concurrentes
WORKERS_TEST_1000 = 10      # Test de 1,000 artículos
WORKERS_TEST_10000 = 50     # Test de 10,000 artículos

# Límites de tiempo (segundos)
TIEMPO_MAX_10000 = 300      # 5 minutos para 10,000 artículos

# Requisitos de throughput
REQUISITO_REQ_MIN = 2000    # 2,000 req/min

# Umbrales de éxito
UMBRAL_EXITO_PCT = 95       # 95% de artículos creados exitosamente
UMBRAL_ERROR_4XX = 5        # Máximo 5% de errores 4xx
UMBRAL_ERROR_5XX = 1        # Máximo 1% de errores 5xx


# =============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN (si aplica)
# =============================================================================

# API Key (si usas API Gateway con API Key)
# API_KEY = "your-api-key-here"
# HEADERS = {
#     "Content-Type": "application/json",
#     "x-api-key": API_KEY
# }

# Bearer Token (si usas OAuth/JWT)
# AUTH_TOKEN = "your-jwt-token-here"
# HEADERS = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {AUTH_TOKEN}"
# }

# Headers por defecto (sin autenticación)
HEADERS = {
    "Content-Type": "application/json"
}


# =============================================================================
# NOTAS DE CONFIGURACIÓN AWS
# =============================================================================
"""
Para usar con AWS Application Load Balancer:

1. **Crear ALB**:
   - Tipo: Application Load Balancer
   - Scheme: Internet-facing
   - IP address type: IPv4
   - Listeners: HTTP (80) y/o HTTPS (443)
   - Target Group: Instancias EC2 con Django

2. **Configurar Target Group**:
   - Protocol: HTTP
   - Port: 8000 (o el puerto de tu aplicación)
   - Health checks: /inventario/api/productos/ o similar
   - Health check interval: 30 segundos
   - Healthy threshold: 2
   - Unhealthy threshold: 2

3. **Auto Scaling Group** (recomendado):
   - Min instances: 2
   - Desired instances: 4
   - Max instances: 10
   - Scaling policy: Target tracking
   - Metric: Request count per target
   - Target value: 500 requests/target

4. **RDS PostgreSQL** (para producción):
   - Instance class: db.t3.medium o superior
   - Multi-AZ: Sí (alta disponibilidad)
   - Storage: 100 GB SSD (gp3)
   - Backup retention: 7 días
   - Enable Performance Insights: Sí

5. **Configuración Django** (settings.py):
   ```python
   ALLOWED_HOSTS = [
       'your-alb-name-123456789.us-east-1.elb.amazonaws.com',
       'api.tudominio.com'
   ]
   
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('DB_NAME'),
           'USER': os.environ.get('DB_USER'),
           'PASSWORD': os.environ.get('DB_PASSWORD'),
           'HOST': os.environ.get('DB_HOST'),  # RDS endpoint
           'PORT': '5432',
           'OPTIONS': {
               'connect_timeout': 10,
           }
       }
   }
   ```

6. **Variables de entorno EC2**:
   - Crear archivo .env o usar Parameter Store
   - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST
   - SECRET_KEY, DEBUG=False

7. **Ejecutar tests desde local contra AWS**:
   ```bash
   # Cambiar BASE_URL en este archivo
   # Asegurarse que el Security Group del ALB permite tu IP
   python manage.py test tests.test_carga_masiva_articulos
   ```

8. **Monitoreo** (CloudWatch):
   - ALB: TargetResponseTime, RequestCount, HTTPCode_Target_4XX_Count
   - EC2: CPUUtilization, NetworkIn, NetworkOut
   - RDS: DatabaseConnections, ReadLatency, WriteLatency

9. **Costos aproximados** (us-east-1, on-demand):
   - ALB: ~$22/mes (básico)
   - EC2 t3.medium x4: ~$120/mes
   - RDS db.t3.medium: ~$75/mes
   - **Total estimado: ~$220/mes**
   
   Para reducir costos:
   - Usar Reserved Instances (40% descuento)
   - Usar Savings Plans (hasta 72% descuento)
   - Escalar a 0 instancias en horarios no laborales
"""
