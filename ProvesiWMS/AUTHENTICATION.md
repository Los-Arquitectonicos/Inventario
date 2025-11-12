# 🔐 Sistema de Autenticación ProvesiWMS

## Resumen
ProvesiWMS implementa un sistema de autenticación robusto usando **Django Authentication + JWT** optimizado para **despliegue en AWS**. El sistema cumple con los requerimientos de seguridad para prevenir sniffing y modificaciones no autorizadas.

## ✅ Requerimientos Cumplidos

### 1. **Prevención de Sniffing**
- ✅ **HTTPS obligatorio** en producción
- ✅ Configuraciones SSL/TLS seguras
- ✅ Headers de seguridad (HSTS, XSS Protection, etc.)
- ✅ Cookies seguras con HttpOnly

### 2. **Prevención de Modificaciones No Autorizadas**
- ✅ Autenticación JWT obligatoria para APIs sensibles
- ✅ Sistema de permisos basado en roles
- ✅ Middleware CSRF habilitado
- ✅ Auditoría de accesos

## 🏗️ Arquitectura del Sistema

### **Componentes Principales**

1. **Django Authentication**: Sistema base de usuarios
2. **JWT Tokens**: Autenticación stateless para APIs
3. **Sistema de Roles**: Control granular de permisos
4. **HTTPS**: Cifrado de comunicaciones
5. **Logging de Seguridad**: Auditoría de accesos

### **Flujo de Autenticación**

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant DB
    
    Client->>API: POST /auth/login (credentials)
    API->>Auth: Validate credentials
    Auth->>DB: Check user
    DB-->>Auth: User data
    Auth-->>API: JWT tokens
    API-->>Client: Access + Refresh tokens
    
    Client->>API: Request with Bearer token
    API->>Auth: Validate JWT
    Auth-->>API: User permissions
    API-->>Client: Protected data
```

## 🎯 Roles y Permisos

### **Admin**
- ✅ Crear/eliminar usuarios
- ✅ Modificar todos los datos
- ✅ Ver todos los datos
- ✅ Acceder a reportes
- ✅ Gestionar inventario completo

### **Gerente**
- ❌ Crear/eliminar usuarios
- ✅ Modificar datos operativos
- ✅ Ver todos los datos
- ✅ Acceder a reportes
- ✅ Gestionar pedidos y clientes

### **Supervisor**
- ❌ Crear usuarios
- ❌ Modificar datos críticos
- ✅ Ver datos operativos
- ✅ Gestionar inventario básico
- ✅ Gestionar pedidos

### **Empleado**
- ❌ Modificar datos
- ❌ Ver datos sensibles
- ❌ Acceder a reportes
- ✅ Solo consultas básicas

## 🚀 Despliegue en AWS

### **1. Preparación del Entorno**

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_HOST=your-rds-endpoint
export DATABASE_NAME=inventario_db
export DATABASE_USER=your-db-user
export DATABASE_PASSWORD=your-secure-password
export SECRET_KEY=your-ultra-secure-secret-key
export DEBUG=False
```

### **2. Configuración de Base de Datos**

```bash
# Aplicar migraciones
python manage.py migrate

# Crear usuarios iniciales
python setup_users.py
```

### **3. Configuración HTTPS en AWS**

#### **Application Load Balancer (ALB)**
```yaml
# Terraform o CloudFormation
resource "aws_lb_listener" "app_https" {
  load_balancer_arn = aws_lb.app.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.app.arn
}
```

#### **CloudFront (Opcional)**
```yaml
resource "aws_cloudfront_distribution" "app" {
  viewer_protocol_policy = "redirect-to-https"
  # Configuración adicional...
}
```

### **4. Variables de Entorno en AWS**

```bash
# EC2 / ECS / Elastic Beanstalk
DATABASE_HOST=your-rds.region.rds.amazonaws.com
DATABASE_NAME=inventario_db
DATABASE_USER=provesi_user
DATABASE_PASSWORD=secure_password_123
SECRET_KEY=django-insecure-replacement-key
DEBUG=False
```

## 📡 Endpoints de Autenticación

### **Login**
```http
POST /inventario/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "ProvesiAdmin2024!"
}
```

**Respuesta:**
```json
{
  "success": true,
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "email": "admin@provesi.com"
  },
  "expires_in": 3600
}
```

### **Acceso a APIs Protegidas**
```http
GET /inventario/api/pedidos/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### **Logout**
```http
POST /inventario/auth/logout/
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "refresh": "your-refresh-token"
}
```

### **Refresh Token**
```http
POST /inventario/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "your-refresh-token"
}
```

## 🔧 APIs Protegidas

### **Nivel de Protección por Endpoint**

| Endpoint | Autenticación | Permiso Requerido | Roles Permitidos |
|----------|---------------|-------------------|------------------|
| `GET /api/pedidos/` | ✅ JWT | `can_view_all_data` | admin, gerente, supervisor |
| `POST /inventario/pedidos/crear/` | ✅ JWT | `can_manage_orders` | admin, gerente, supervisor |
| `PUT /inventario/pedidos/{id}/actualizar-estado/` | ✅ JWT | `can_manage_orders` | admin, gerente, supervisor |
| `GET /api/usuarios/` | ✅ JWT | - | admin, gerente |
| `DELETE /api/articulos/eliminar_todos/` | ✅ JWT | - | admin |
| `DELETE /api/productos/eliminar_todos/` | ✅ JWT | - | admin |
| `POST /inventario/productos/crear/` | ✅ JWT | `can_manage_inventory` | admin, gerente, supervisor |
| `POST /inventario/clientes/crear/` | ✅ JWT | `can_manage_clients` | admin, gerente |

## 🛡️ Configuraciones de Seguridad

### **HTTPS y SSL**
```python
# settings.py - Configuraciones automáticas para AWS
SECURE_SSL_REDIRECT = not DEBUG  # Force HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### **Cookies Seguras**
```python
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
```

### **CORS y CSRF**
```python
CSRF_TRUSTED_ORIGINS = [
    'https://*.elb.amazonaws.com',
    'https://*.compute.amazonaws.com',
]
```

## 📊 Logging y Auditoría

### **Logs de Seguridad**
```python
# Configuración automática en settings.py
LOGGING = {
    'loggers': {
        'django.security': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
        },
        'inventario': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    }
}
```

### **Archivos de Log**
- `/tmp/django.log` - Logs generales
- `/tmp/django-security.log` - Logs de seguridad
- CloudWatch (AWS) - Monitoreo en tiempo real

## 🧪 Testing del Sistema

### **1. Test de Autenticación**
```bash
# Login exitoso
curl -X POST https://your-domain/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ProvesiAdmin2024!"}'

# Verificar token
curl -X POST https://your-domain/inventario/auth/verify/ \
  -H "Content-Type: application/json" \
  -d '{"token":"your-access-token"}'
```

### **2. Test de Protección de APIs**
```bash
# Sin token (debe fallar con 401)
curl -X GET https://your-domain/inventario/api/pedidos/

# Con token válido (debe funcionar)
curl -X GET https://your-domain/inventario/api/pedidos/ \
  -H "Authorization: Bearer your-access-token"

# Con rol insuficiente (debe fallar con 403)
curl -X DELETE https://your-domain/inventario/api/productos/eliminar_todos/ \
  -H "Authorization: Bearer employee-token"
```

### **3. Test de HTTPS**
```bash
# Verificar redirección HTTP -> HTTPS
curl -I http://your-domain/inventario/
# Debe retornar 301/302 redirect a HTTPS

# Verificar headers de seguridad
curl -I https://your-domain/inventario/
# Debe incluir: Strict-Transport-Security, X-Content-Type-Options, etc.
```

## ⚡ Usuarios de Prueba

El script `setup_users.py` crea usuarios de prueba:

| Usuario | Contraseña | Rol | Permisos |
|---------|------------|-----|----------|
| `admin` | `ProvesiAdmin2024!` | admin | Todos los permisos |
| `gerente` | `Gerente2024!` | gerente | Gestión operativa |
| `empleado` | `Empleado2024!` | empleado | Solo consultas |

## 🚨 Consideraciones de Seguridad

### **Producción**
1. ✅ Cambiar todas las contraseñas por defecto
2. ✅ Usar variables de entorno para secretos
3. ✅ Configurar certificado SSL válido
4. ✅ Habilitar CloudTrail para auditoría
5. ✅ Configurar WAF para protección adicional

### **Monitoreo**
1. ✅ CloudWatch para logs
2. ✅ Alertas por intentos de acceso fallidos
3. ✅ Monitoreo de patrones de uso anómalos
4. ✅ Backup automático de base de datos

## 🎯 Próximos Pasos

1. **Deploy en AWS**: Usar Terraform/CloudFormation
2. **Certificado SSL**: AWS Certificate Manager
3. **WAF**: Protección adicional contra ataques
4. **Backup**: RDS Backup automático
5. **Monitoring**: CloudWatch + SNS alerts

---

**✅ Sistema Completamente Funcional para AWS**
- 🔒 HTTPS forzado en producción
- 🎫 JWT authentication robusto
- 👥 Sistema de roles granular
- 📊 Logging y auditoría completos
- 🛡️ Protección contra sniffing y modificaciones no autorizadas