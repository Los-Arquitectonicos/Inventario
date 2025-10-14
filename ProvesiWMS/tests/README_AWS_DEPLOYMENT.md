# Guía de Deployment en AWS con Load Testing

## 📋 Resumen Ejecutivo

Esta guía te ayudará a:
1. **Desplegar** tu aplicación Django en AWS con Application Load Balancer
2. **Ejecutar** los tests de carga masiva contra el entorno AWS
3. **Monitorear** el rendimiento y escalabilidad
4. **Optimizar** costos y performance

---

## 🎯 Arquitectura Recomendada

```
Internet
   ↓
Route 53 (DNS)
   ↓
Application Load Balancer (ALB)
   ↓
Target Group (Health Checks)
   ↓
Auto Scaling Group
   ├─ EC2 Instance 1 (Django + Gunicorn)
   ├─ EC2 Instance 2 (Django + Gunicorn)
   ├─ EC2 Instance 3 (Django + Gunicorn)
   └─ EC2 Instance 4 (Django + Gunicorn)
   ↓
RDS PostgreSQL (Multi-AZ)
```

---

## 🚀 Paso 1: Configurar RDS PostgreSQL

### 1.1 Crear Base de Datos

```bash
# En AWS Console → RDS → Create Database
Engine: PostgreSQL 15.x
Template: Production
DB Instance Class: db.t3.medium (2 vCPU, 4 GB RAM)
Storage: 100 GB gp3
Multi-AZ: Yes (alta disponibilidad)
DB Name: provesi_wms
Master username: postgres
Master password: [crear contraseña segura]
VPC: default (o tu VPC personalizada)
Public access: No
Security group: rds-postgres-sg (crear nuevo)
```

### 1.2 Configurar Security Group

```bash
# En EC2 → Security Groups → Create Security Group
Name: rds-postgres-sg
Inbound rules:
  - Type: PostgreSQL (5432)
    Source: ec2-instances-sg (security group de EC2)
    Description: Allow PostgreSQL from EC2 instances
```

---

## 🖥️ Paso 2: Configurar EC2 Instances

### 2.1 Crear AMI Base (una sola vez)

```bash
# Lanzar instancia temporal para crear AMI
Instance type: t3.medium
AMI: Ubuntu Server 22.04 LTS
Storage: 20 GB gp3

# Conectarse por SSH
ssh -i "tu-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# Instalar dependencias
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql-client nginx git

# Instalar Gunicorn
pip3 install gunicorn

# Clonar tu repositorio
cd /home/ubuntu
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario/ProvesiWMS

# Crear ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install psycopg2-binary gunicorn

# Configurar variables de entorno
sudo nano /etc/environment
```

Agregar:
```bash
DB_NAME="provesi_wms"
DB_USER="postgres"
DB_PASSWORD="tu-password-seguro"
DB_HOST="your-rds-endpoint.rds.amazonaws.com"
SECRET_KEY="tu-secret-key-django"
DEBUG="False"
ALLOWED_HOSTS="*"
```

### 2.2 Configurar Gunicorn

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/gunicorn.service
```

Contenido:
```ini
[Unit]
Description=Gunicorn daemon for ProvesiWMS
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/Inventario/ProvesiWMS
Environment="PATH=/home/ubuntu/Inventario/ProvesiWMS/venv/bin"
EnvironmentFile=/etc/environment
ExecStart=/home/ubuntu/Inventario/ProvesiWMS/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    wms.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y arrancar
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

### 2.3 Migrar Base de Datos

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput

# Crear superusuario (opcional)
python manage.py createsuperuser
```

### 2.4 Crear AMI

```bash
# En AWS Console → EC2 → Instances
# Selecciona tu instancia → Actions → Image and templates → Create image
Name: provesi-wms-v1
Description: Django + Gunicorn + PostgreSQL client
```

---

## ⚖️ Paso 3: Configurar Application Load Balancer

### 3.1 Crear Target Group

```bash
# En EC2 → Target Groups → Create target group
Target type: Instances
Name: provesi-wms-targets
Protocol: HTTP
Port: 8000
VPC: [tu VPC]

Health check:
  Protocol: HTTP
  Path: /inventario/api/productos/
  Success codes: 200
  Interval: 30 seconds
  Timeout: 5 seconds
  Healthy threshold: 2
  Unhealthy threshold: 2
```

### 3.2 Crear ALB

```bash
# En EC2 → Load Balancers → Create Load Balancer
Type: Application Load Balancer
Name: provesi-wms-alb
Scheme: Internet-facing
IP address type: IPv4

Network mapping:
  VPC: [tu VPC]
  Mappings: Selecciona al menos 2 AZs
  
Security groups: alb-sg (crear nuevo)
  Inbound:
    - HTTP (80) from 0.0.0.0/0
    - HTTPS (443) from 0.0.0.0/0 (si usas SSL)

Listeners:
  - Protocol: HTTP, Port: 80
    Default action: Forward to provesi-wms-targets
```

### 3.3 Obtener URL del ALB

```bash
# En EC2 → Load Balancers → Selecciona tu ALB
# Copia el "DNS name":
provesi-wms-alb-123456789.us-east-1.elb.amazonaws.com
```

---

## 📈 Paso 4: Configurar Auto Scaling

### 4.1 Crear Launch Template

```bash
# En EC2 → Launch Templates → Create launch template
Name: provesi-wms-template
AMI: provesi-wms-v1 (la que creaste)
Instance type: t3.medium
Key pair: [tu key pair]
Network settings:
  Security groups: ec2-instances-sg (crear nuevo)
    Inbound:
      - HTTP (8000) from alb-sg
      - SSH (22) from tu IP
```

### 4.2 Crear Auto Scaling Group

```bash
# En EC2 → Auto Scaling Groups → Create Auto Scaling group
Name: provesi-wms-asg
Launch template: provesi-wms-template
VPC: [tu VPC]
Subnets: Selecciona al menos 2 AZs

Load balancing:
  Attach to existing load balancer
  Choose target group: provesi-wms-targets

Health checks:
  ELB health check: Enabled
  Health check grace period: 300 seconds

Group size:
  Desired: 4
  Minimum: 2
  Maximum: 10

Scaling policies:
  - Target tracking scaling policy
  - Metric: Request count per target
  - Target value: 500
  - Instances need: 300 seconds warm up
```

---

## 🧪 Paso 5: Ejecutar Tests de Carga

### 5.1 Configurar URL

Edita `tests/config_entornos.py`:

```python
# Comenta la línea local:
# BASE_URL = "http://127.0.0.1:8000"

# Descomenta y actualiza con tu ALB:
BASE_URL = "http://provesi-wms-alb-123456789.us-east-1.elb.amazonaws.com"
TIMEOUT = 60  # Mayor timeout para red remota
```

### 5.2 Preparar Datos Base

**IMPORTANTE**: Antes de correr tests, necesitas crear datos base en RDS:

```bash
# Opción A: Desde tu máquina local (si RDS es público)
# Actualiza settings.py temporalmente con credenciales RDS
python manage.py shell

# Opción B: Desde una instancia EC2
ssh -i "tu-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
cd /home/ubuntu/Inventario/ProvesiWMS
source venv/bin/activate
python manage.py shell
```

En el shell:
```python
from inventario.models import Bodega, UbicacionBodega, Producto

# Crear bodega
bodega = Bodega.objects.create(
    nombre="Bodega AWS Test",
    ciudad="Virginia",
    direccion="AWS us-east-1"
)

# Crear ubicación con capacidad para 20,000 artículos
ubicacion = UbicacionBodega.objects.create(
    bodega=bodega,
    pasillo="A",
    estante="1",
    nivel="1",
    capacidad_total=20000,
    capacidad_disponible=20000
)

# Crear producto
producto = Producto.objects.create(
    codigo="PROD-001",
    nombre="Producto Test AWS",
    precio_unitario=10.00
)

print(f"Bodega ID: {bodega.id}")
print(f"Ubicación ID: {ubicacion.id}")
print(f"Producto ID: {producto.id}")
```

### 5.3 Actualizar Test con IDs

Edita `tests/test_carga_masiva_articulos.py` en el método `setUp`:

```python
def setUp(self):
    """Preparar datos base para las pruebas"""
    # Para AWS: Usa IDs existentes en RDS
    self.bodega = Bodega.objects.get(id=1)  # Usa el ID que obtuviste
    self.ubicacion = UbicacionBodega.objects.get(id=1)
    self.producto = Producto.objects.get(id=1)
```

### 5.4 Ejecutar Tests

```bash
# Desde tu máquina local
cd /Users/pedropablosanintrujillo/GitHub/Inventario/ProvesiWMS

# Test de 1,000 artículos (10 workers)
python manage.py test tests.test_carga_masiva_articulos.TestCargaMasivaArticulos.test_02_concurrente_1000 -v 2

# Test de 10,000 artículos (50 workers)
python manage.py test tests.test_carga_masiva_articulos.TestCargaMasivaArticulos.test_03_objetivo_10000 -v 2
```

---

## 📊 Paso 6: Monitoreo con CloudWatch

### 6.1 Métricas Importantes

**ALB Metrics:**
- `TargetResponseTime`: Tiempo de respuesta (debe ser < 500ms)
- `RequestCount`: Número de requests (objetivo: 2000/min)
- `HTTPCode_Target_2XX_Count`: Respuestas exitosas
- `HTTPCode_Target_4XX_Count`: Errores del cliente (debe ser < 5%)
- `HTTPCode_Target_5XX_Count`: Errores del servidor (debe ser < 1%)
- `HealthyHostCount`: Instancias saludables
- `UnHealthyHostCount`: Instancias no saludables

**EC2 Metrics:**
- `CPUUtilization`: Uso de CPU (< 80%)
- `NetworkIn/Out`: Tráfico de red
- `StatusCheckFailed`: Fallos de health checks

**RDS Metrics:**
- `DatabaseConnections`: Conexiones activas (< 100)
- `ReadLatency/WriteLatency`: Latencia (< 10ms)
- `CPUUtilization`: CPU de RDS (< 80%)
- `FreeableMemory`: Memoria disponible

### 6.2 Crear Alarmas

```bash
# En CloudWatch → Alarms → Create alarm

Alarma 1: High ALB Error Rate
  Metric: HTTPCode_Target_5XX_Count
  Statistic: Sum
  Period: 5 minutes
  Threshold: > 50 (más de 50 errores en 5 min)
  Actions: Send SNS notification

Alarma 2: High Response Time
  Metric: TargetResponseTime
  Statistic: Average
  Period: 5 minutes
  Threshold: > 1 second
  Actions: Send SNS notification

Alarma 3: No Healthy Instances
  Metric: HealthyHostCount
  Statistic: Minimum
  Period: 1 minute
  Threshold: < 1
  Actions: Send SNS notification + Scale out
```

---

## 💰 Paso 7: Optimización de Costos

### 7.1 Estimación de Costos (us-east-1)

**Configuración Base:**
```
ALB:                    $22.00/mes (base)
EC2 t3.medium x4:      $120.00/mes ($30 cada una)
RDS db.t3.medium:       $75.00/mes
Data Transfer:          $20.00/mes (estimado)
CloudWatch:             $10.00/mes
----------------------------------------------
TOTAL:                 $247.00/mes
```

**Con Reserved Instances (1 año, sin upfront):**
```
EC2 t3.medium x4:       $72.00/mes (40% descuento)
RDS db.t3.medium:       $45.00/mes (40% descuento)
----------------------------------------------
TOTAL OPTIMIZADO:      $174.00/mes (30% ahorro)
```

### 7.2 Estrategias de Ahorro

**1. Usar Spot Instances para workers:**
```python
# En Auto Scaling Group → Purchase options
On-Demand: 50%
Spot: 50% (hasta 90% descuento)
```

**2. Escalar a 0 en horarios no laborales:**
```bash
# Crear scheduled actions en ASG
Lunes-Viernes 8am: Min=2, Desired=4, Max=10
Lunes-Viernes 6pm: Min=0, Desired=0, Max=10
```

**3. Usar RDS Aurora Serverless v2:**
```
Aurora Serverless v2: Escala automáticamente
Min capacity: 0.5 ACU ($0.12/hora)
Max capacity: 4 ACU ($0.96/hora)
Costo promedio: ~$50/mes (33% ahorro vs RDS normal)
```

---

## 🔒 Paso 8: Seguridad

### 8.1 Configurar HTTPS

```bash
# 1. Solicitar certificado en ACM
Certificate Manager → Request certificate
Domain name: api.tudominio.com
Validation: DNS validation

# 2. Agregar listener HTTPS en ALB
Port: 443
Protocol: HTTPS
Certificate: Selecciona tu certificado ACM
Default action: Forward to provesi-wms-targets

# 3. Redirigir HTTP a HTTPS
Listener HTTP:80 → Edit
Default action: Redirect to HTTPS:443
```

### 8.2 Configurar WAF

```bash
# En WAF → Create web ACL
Name: provesi-wms-waf
Resource type: Regional (ALB)
Associated AWS resources: Selecciona tu ALB

Rules:
  - AWS Managed: Core rule set
  - AWS Managed: Known bad inputs
  - Rate limiting: 2000 requests per 5 minutes per IP
```

---

## ✅ Checklist de Deployment

- [ ] RDS PostgreSQL creado y configurado
- [ ] AMI base creada con Django + Gunicorn
- [ ] Security groups configurados correctamente
- [ ] ALB creado con target group
- [ ] Auto Scaling Group configurado (2-10 instancias)
- [ ] Health checks funcionando
- [ ] Base de datos migrada
- [ ] Datos base creados (Bodega, Ubicación, Producto)
- [ ] `config_entornos.py` actualizado con URL del ALB
- [ ] Tests ejecutados exitosamente
- [ ] CloudWatch alarms configuradas
- [ ] HTTPS configurado (opcional pero recomendado)
- [ ] WAF configurado (opcional)

---

## 🎓 Resultados Esperados

Después del deployment, deberías obtener:

**Test de 1,000 artículos (10 workers):**
- ✅ Tiempo total: < 30 segundos
- ✅ Throughput: > 2,000 req/min
- ✅ Tasa de éxito: > 95%
- ✅ Response time P95: < 500ms

**Test de 10,000 artículos (50 workers):**
- ✅ Tiempo total: < 5 minutos (requerimiento arquitectónico)
- ✅ Throughput: > 2,000 req/min
- ✅ Tasa de éxito: > 95%
- ✅ Response time P95: < 1 segundo
- ✅ Sin degradación de performance
- ✅ Datos consistentes (artículos creados = capacidad usada)

---

## 🆘 Troubleshooting

### Problema: "Connection refused"
```bash
# Verificar security groups
# ALB debe permitir tu IP en puerto 80/443
# EC2 debe permitir ALB en puerto 8000
```

### Problema: "502 Bad Gateway"
```bash
# Verificar que Gunicorn esté corriendo
ssh -i "tu-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
sudo systemctl status gunicorn

# Ver logs
sudo journalctl -u gunicorn -n 100 --no-pager
```

### Problema: Health checks failing
```bash
# Verificar que el endpoint responda
curl http://localhost:8000/inventario/api/productos/

# Verificar ALLOWED_HOSTS en settings.py
ALLOWED_HOSTS = ['*']  # O específicamente tu ALB DNS
```

### Problema: Tests con timeout
```bash
# Aumentar TIMEOUT en config_entornos.py
TIMEOUT = 120  # 2 minutos

# Verificar que ASG tenga suficientes instancias
# Verificar que RDS tenga suficientes conexiones
```

---

## 📚 Referencias

- [AWS ALB Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

---

¿Necesitas ayuda? Contacta al equipo de DevOps o abre un issue en el repositorio.
