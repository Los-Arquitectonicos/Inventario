# Plan: Microservicio de Service Discovery con Kong API Gateway

Este plan detalla la implementación de Kong como API Gateway centralizado para gestionar el enrutamiento y descubrimiento de servicios en ProvesiWMS, integrándose con la infraestructura AWS existente.

## Arquitectura Propuesta

```
Internet → ALB (HTTPS/443) → Kong Gateway (EC2 t3.small) → Servicios Backend
                                         ├→ Django App (puerto 8000)
                                         ├→ Notifications (puerto 3001)
                                         ├→ Analytics (Lambda HTTP)
                                         ├→ Order Workflow (puerto 3002)
                                         └→ Config Service (puerto 3003)
```

Kong actuará como **único punto de entrada** para todos los microservicios, proporcionando:
- **Enrutamiento centralizado** basado en paths (`/api`, `/notifications`, `/analytics`)
- **Autenticación JWT unificada** (validación en Kong, generación en Django)
- **Rate limiting y CORS** aplicados de forma consistente
- **Logging centralizado** para monitoreo

## Tecnologías y Decisiones Clave

- **Edición:** Kong Gateway OSS (código abierto) - Suficiente para todas las necesidades actuales
- **Modo:** DB-less (configuración declarativa YAML) - Sin dependencia de base de datos adicional
- **Infraestructura:** EC2 t3.small (2 vCPU, 2GB RAM) - Capaz de manejar 100-500 req/s
- **SSL:** ALB termina HTTPS, Kong usa HTTP internamente - Simplifica gestión de certificados
- **Despliegue:** Terraform (consistente con infraestructura actual)

## Estructura de Archivos

```
ProvesiWMS/
├── terraform/
│   ├── main.tf              # [MODIFICAR] Agregar recursos de Kong
│   ├── variables.tf         # [MODIFICAR] Agregar variables de Kong
│   ├── outputs.tf           # [MODIFICAR] Agregar outputs de Kong
│   └── kong/
│       ├── kong_instance.tf     # Nueva instancia EC2 para Kong
│       ├── kong_security_group.tf  # Reglas de seguridad
│       └── kong_alb_integration.tf # Integración con ALB existente
└── kong/
    ├── kong.yml             # Configuración declarativa de servicios
    ├── kong.conf            # Configuración de Kong (variables de entorno)
    └── README.md            # Documentación de uso
```

## Recursos de Terraform a Crear

### 1. Instancia EC2 para Kong

**Archivo:** `terraform/kong/kong_instance.tf`

```hcl
resource "aws_instance" "kong_gateway" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.small"
  vpc_security_group_ids = [aws_security_group.kong.id]
  associate_public_ip_address = false  # Kong solo accesible desde ALB
  
  user_data = <<-EOT
    #!/bin/bash
    # Instalar Kong OSS 3.5
    curl -Lo kong.deb "https://download.konghq.com/gateway-3.x-ubuntu-noble/pool/all/k/kong/kong_3.5.0_amd64.deb"
    sudo dpkg -i kong.deb
    
    # Copiar configuración
    sudo mkdir -p /etc/kong
    sudo tee /etc/kong/kong.yml > /dev/null <<'KONGCONFIG'
    ${file("${path.module}/../kong/kong.yml")}
    KONGCONFIG
    
    # Variables de entorno Kong
    export KONG_DATABASE=off
    export KONG_DECLARATIVE_CONFIG=/etc/kong/kong.yml
    export KONG_PROXY_LISTEN="0.0.0.0:8000, 0.0.0.0:8443 ssl"
    export KONG_ADMIN_LISTEN="127.0.0.1:8001"
    export KONG_LOG_LEVEL=info
    
    # Iniciar Kong
    sudo kong start
    
    # Healthcheck
    curl -f http://localhost:8000/status || exit 1
  EOT
  
  tags = {
    Name = "${var.project_prefix}-kong-gateway"
    Role = "api-gateway"
  }
}
```

### 2. Security Group para Kong

**Archivo:** `terraform/kong/kong_security_group.tf`

```hcl
resource "aws_security_group" "kong" {
  name        = "${var.project_prefix}-kong-sg"
  description = "Security group for Kong API Gateway"
  vpc_id      = data.aws_vpc.default.id
  
  # Proxy HTTP desde ALB
  ingress {
    description     = "Kong proxy from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Proxy HTTPS desde ALB (futuro)
  ingress {
    description     = "Kong proxy SSL from ALB"
    from_port       = 8443
    to_port         = 8443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Admin API (solo localhost, acceso vía SSH tunnel)
  ingress {
    description = "SSH for management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restringir en producción
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_prefix}-kong-sg"
  }
}

# Permitir que Kong acceda a servidores Django
resource "aws_security_group_rule" "django_from_kong" {
  security_group_id        = aws_security_group.app.id
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access Django servers"
}
```

### 3. Integración con ALB

**Archivo:** `terraform/kong/kong_alb_integration.tf`

```hcl
# Target Group para Kong
resource "aws_lb_target_group" "kong" {
  name     = "${var.project_prefix}-kong-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id
  
  health_check {
    enabled             = true
    path                = "/status"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }
  
  tags = {
    Name = "${var.project_prefix}-kong-tg"
  }
}

# Registrar instancia Kong en Target Group
resource "aws_lb_target_group_attachment" "kong" {
  target_group_arn = aws_lb_target_group.kong.arn
  target_id        = aws_instance.kong_gateway.id
  port             = 8000
}

# Modificar listener HTTPS para apuntar a Kong
resource "aws_lb_listener_rule" "kong_routing" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong.arn
  }
  
  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

## Configuración de Kong (kong.yml)

**Archivo:** `kong/kong.yml`

```yaml
_format_version: "3.0"

# ==========================================
# CONSUMERS (Usuarios/Apps que consumen API)
# ==========================================
consumers:
  - username: django-backend
    jwt_secrets:
      - key: django-jwt-key
        secret: "${DJANGO_SECRET_KEY}"  # Mismo secret que Django
        algorithm: HS256

# ==========================================
# SERVICES & ROUTES
# ==========================================

# Service 1: Django Backend (existente)
services:
  - name: django-api
    url: http://${DJANGO_PRIVATE_IP_1}:8000  # IP privada del servidor Django
    retries: 3
    connect_timeout: 5000
    routes:
      - name: django-api-routes
        paths:
          - /api
          - /inventario
          - /admin
        strip_path: false
        preserve_host: true
    plugins:
      - name: jwt
        config:
          claims_to_verify: ["exp"]
          header_names: ["Authorization"]
          uri_param_names: ["jwt"]
      - name: rate-limiting
        config:
          minute: 200
          policy: local
      - name: cors
        config:
          origins: ["*"]
          credentials: true
          max_age: 3600

# Service 2: Notifications Microservice
services:
  - name: notifications
    url: http://${NOTIFICATIONS_PRIVATE_IP}:3001
    routes:
      - name: notifications-routes
        paths:
          - /notifications
        strip_path: false
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 100

# Service 3: Analytics (Lambda Serverless)
services:
  - name: analytics
    url: ${ANALYTICS_LAMBDA_URL}
    routes:
      - name: analytics-routes
        paths:
          - /analytics
          - /reports
    plugins:
      - name: jwt
      - name: request-transformer
        config:
          add:
            headers:
              - X-Service-Origin:kong-gateway

# Service 4: Order Workflow
services:
  - name: workflow
    url: http://${WORKFLOW_PRIVATE_IP}:3002
    routes:
      - name: workflow-routes
        paths:
          - /workflow
          - /orders/status
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 150

# Service 5: Config & Feature Flags
services:
  - name: config-service
    url: http://${CONFIG_PRIVATE_IP}:3003
    routes:
      - name: config-routes
        paths:
          - /config
          - /features
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 50

# ==========================================
# GLOBAL PLUGINS
# ==========================================
plugins:
  - name: correlation-id
    config:
      header_name: X-Kong-Request-ID
      generator: uuid
  
  - name: request-id
  
  - name: file-log
    config:
      path: /var/log/kong/access.log
      reopen: true
```

## Variables de Terraform a Agregar

**Archivo:** `terraform/variables.tf` (agregar al final)

```hcl
# ===================================
# KONG API GATEWAY VARIABLES
# ===================================

variable "kong_instance_type" {
  description = "EC2 instance type for Kong Gateway"
  type        = string
  default     = "t3.small"
}

variable "kong_version" {
  description = "Kong Gateway version to install"
  type        = string
  default     = "3.5.0"
}

variable "kong_log_level" {
  description = "Kong logging level (debug, info, notice, warn, error, crit)"
  type        = string
  default     = "info"
}

variable "enable_kong_admin_api" {
  description = "Enable Kong Admin API on public interface (not recommended for production)"
  type        = bool
  default     = false
}
```

## Outputs a Agregar

**Archivo:** `terraform/outputs.tf` (agregar al final)

```hcl
output "kong_gateway_private_ip" {
  description = "Private IP of Kong Gateway instance"
  value       = aws_instance.kong_gateway.private_ip
}

output "kong_admin_ssh" {
  description = "SSH command to access Kong Gateway for administration"
  value       = "ssh ubuntu@${aws_instance.kong_gateway.public_ip}"
}

output "kong_health_check_url" {
  description = "Kong health check endpoint (via ALB)"
  value       = "https://${aws_lb.main.dns_name}/status"
}
```

## Pasos de Implementación

### Fase 1: Setup Básico de Kong (Semana 1)
1. **Crear archivos de configuración:** Crear carpeta `kong/` con `kong.yml` básico (solo servicio Django)
2. **Actualizar Terraform:** Agregar módulo `kong/` dentro de `terraform/`
3. **Desplegar Kong:** `terraform apply` para crear instancia EC2 Kong
4. **Verificar instalación:** SSH a Kong, comprobar `kong health`
5. **Probar enrutamiento:** Acceder a Django a través de Kong vía ALB

### Fase 2: Integración JWT y Seguridad (Semana 2)
1. **Configurar consumer JWT:** Agregar consumer en `kong.yml` con secret de Django
2. **Aplicar plugin JWT:** Activar validación JWT en ruta Django
3. **Probar autenticación:** Hacer requests con token JWT, verificar validación
4. **Configurar rate limiting:** Aplicar límites por servicio
5. **Habilitar CORS:** Configurar origins permitidos

### Fase 3: Onboarding de Microservicios (Semanas 3-4)
1. **Agregar Notifications:** Crear service y route en `kong.yml`, actualizar security groups
2. **Agregar Analytics Lambda:** Configurar service con URL de Lambda
3. **Agregar Workflow:** Crear service y route para Order Workflow
4. **Agregar Config Service:** Crear service y route para Config & Feature Flags
5. **Probar integración completa:** Verificar enrutamiento de todos los servicios

### Fase 4: Monitoreo y Optimización (Semana 5)
1. **Configurar logging:** Integrar logs de Kong con CloudWatch
2. **Métricas de rendimiento:** Configurar CloudWatch metrics para Kong
3. **Load testing:** Ejecutar pruebas de carga con Locust
4. **Ajustar rate limits:** Optimizar límites basándose en métricas reales
5. **Documentar endpoints:** Actualizar `API_DOCUMENTATION.md`

## Integración con Django

### Cambios Necesarios en Django (Mínimos)

**Opción A: Django confía en validación de Kong (Recomendado)**
- Kong valida JWT y pasa headers `X-Consumer-Username`, `X-Consumer-ID`
- Django puede leer estos headers en lugar de re-validar JWT
- Reducción de latencia (validación una sola vez en Kong)

**Opción B: Django valida JWT independientemente**
- Kong solo enruta, no valida JWT
- Django mantiene decoradores `@jwt_required` existentes
- Más simple pero duplica validación

**Implementación sugerida (Opción A):**

```python
# inventario/middleware.py (nuevo archivo)
class KongAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Si viene de Kong, confiar en headers
        consumer_username = request.META.get('HTTP_X_CONSUMER_USERNAME')
        if consumer_username:
            # Marcar request como autenticado por Kong
            request.kong_authenticated = True
            request.kong_user = consumer_username
        
        return self.get_response(request)

# wms/settings.py
MIDDLEWARE = [
    # ... existentes
    'inventario.middleware.KongAuthMiddleware',
]
```

## Comandos de Administración

### Acceder a Kong Admin API
```bash
# SSH tunnel para acceder Admin API
ssh -L 8001:localhost:8001 ubuntu@<kong-public-ip>

# En otra terminal, usar Admin API
curl http://localhost:8001/services
curl http://localhost:8001/routes
curl http://localhost:8001/plugins
```

### Recargar configuración
```bash
# SSH a Kong
ssh ubuntu@<kong-public-ip>

# Editar kong.yml
sudo nano /etc/kong/kong.yml

# Recargar configuración sin downtime
sudo kong reload
```

### Ver logs
```bash
# Logs de Kong
sudo tail -f /var/log/kong/error.log
sudo tail -f /var/log/kong/access.log

# Healthcheck
curl http://localhost:8000/status
```

## Consideraciones de Seguridad

1. **Admin API:** Solo accesible vía `localhost` (requiere SSH tunnel)
2. **JWT Secrets:** Almacenar en variables de entorno Terraform (sensibles)
3. **Security Groups:** Kong solo acepta tráfico desde ALB
4. **Rate Limiting:** Proteger endpoints críticos (login, registro)
5. **CORS:** Restringir origins en producción (cambiar de `*` a dominios específicos)

## Métricas y Monitoreo

### Métricas Clave a Monitorear
- **Latencia P95:** Debe mantenerse < 100ms para cumplir objetivo de latencia
- **Throughput:** Requests por segundo por servicio
- **Error Rate:** % de respuestas 4xx/5xx
- **Kong Health:** Uptime de Kong (health check endpoint)

### Integración CloudWatch
```yaml
# Agregar a kong.yml
plugins:
  - name: http-log
    config:
      http_endpoint: https://logs.region.amazonaws.com/...
      method: POST
      content_type: application/json
```

## Costos Estimados

| Recurso | Tipo | Costo Mensual (USD) |
|---------|------|---------------------|
| Kong EC2 | t3.small | ~$15 |
| Data Transfer ALB | Adicional | ~$2-5 |
| **Total Adicional** | | **~$17-20/mes** |

## Ventajas de Esta Arquitectura

✅ **Centralización:** Un único punto de entrada para todos los microservicios  
✅ **Seguridad:** Validación JWT centralizada, rate limiting consistente  
✅ **Observabilidad:** Logs y métricas unificadas  
✅ **Escalabilidad:** Fácil agregar nuevos microservicios (solo actualizar `kong.yml`)  
✅ **Simplicidad:** DB-less mode, sin base de datos adicional  
✅ **Costo-efectivo:** Solo ~$20/mes adicionales

## Consideraciones Adicionales

### Escalabilidad Futura
- **Kong Cluster:** Si se necesita HA, agregar segunda instancia Kong con ALB balanceando entre ambas
- **Modo Database:** Migrar a PostgreSQL si se requiere configuración dinámica frecuente
- **Kong Enterprise:** Si se necesita GUI, RBAC avanzado, soporte oficial

### Alternativas Evaluadas
- ✗ **AWS App Mesh:** Requiere containers/ECS, demasiado complejo
- ✗ **Traefik:** Menos maduro que Kong para use cases de API Gateway
- ✗ **Nginx + Consul:** Más complejo de configurar y mantener
- ✅ **Kong OSS:** Balance perfecto de simplicidad, features y costo
