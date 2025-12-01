# Terraform Infrastructure as Code - ProvesiWMS

Este directorio contiene la infraestructura como código (IaC) para desplegar ProvesiWMS en AWS con **variables preconfiguradas para entorno de pruebas**.

## 🚀 Deployment Rápido

Para un deployment paso a paso desde AWS Dashboard (sin SSH), consulta:

**📖 [DEPLOYMENT_AWS.md](../DEPLOYMENT_AWS.md)**

## Entorno de Pruebas Preconfigurado

- **Variables incluidas**: Todas las configuraciones están en `terraform.tfvars`
- **Sin configuración SSH**: Usa EC2 Instance Connect desde la consola
- **Inicio manual**: Los servidores Django se inician desde la consola EC2
- **Configuración de testing**: Debug habilitado, tokens de larga duración

## Arquitectura

```
Internet (HTTP) → ALB → App Servers (manual start) → PostgreSQL
```

- **Application Load Balancer (ALB)** distribuye tráfico
- **2 instancias EC2** con Django + JWT (inicio manual desde consola)
- **1 instancia EC2** con PostgreSQL preconfigurada
- **Variables de entorno** incluidas para testing

## Variables Preconfiguradas

El archivo `terraform.tfvars` ya incluye:

```hcl
# Instancias optimizadas para testing
instance_type = "t3.medium"
app_server_count = 2

# Base de datos de pruebas
database_password = "ProvesiDB2025!Testing"

# Django configurado para testing  
django_secret_key = "django-testing-secret-..."
environment = "testing"
debug_mode = true

# JWT con tokens de larga duración
jwt_access_token_lifetime_hours = 24
jwt_refresh_token_lifetime_days = 30

# CORS abierto para testing
cors_allowed_origins = "*"
```

## Deployment Simple

```bash
# 1. Clonar en CloudShell
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario/ProvesiWMS/terraform

# 2. Desplegar (variables ya incluidas)
terraform init
terraform apply

# 3. Configurar desde EC2 Console (sin SSH)
# Ver DEPLOYMENT_AWS.md para pasos detallados
```

## Configuración desde EC2 Console

1. **EC2 Console** → **Instances** → **Connect** → **EC2 Instance Connect**
2. **Username**: `ubuntu`
3. **Ejecutar en cada servidor**:
   ```bash
   cd /opt/apps/Inventario/ProvesiWMS
   source ../venv/bin/activate
   sudo python3 manage.py runserver 0.0.0.0:8080
   ```

## Usuarios de Prueba

- **admin/admin123** (Administrador completo)
- **gerente/gerente123** (Gestión de pedidos/productos)
- **supervisor/supervisor123** (Gestión de pedidos)
- **empleado/empleado123** (Solo lectura)

## Costos Estimados (Testing)

- **2x t3.medium** (app): ~$60/mes
- **1x t3.small** (DB): ~$30/mes  
- **ALB**: ~$23/mes
- **Total**: ~$113/mes

## Comandos Útiles

```bash
# Ver outputs después del deployment
terraform output

# Limpiar todo
terraform destroy

# Verificar plan sin aplicar
terraform plan
```

## Archivos Clave

| Archivo | Descripción |
|---------|-------------|
| `terraform.tfvars` | Variables preconfiguradas para testing |
| `main.tf` | Definición de infraestructura AWS |
| `variables.tf` | Definiciones de variables con validación |
| `outputs.tf` | IPs y URLs post-deployment |

## Configuración de Testing vs Producción

### Testing (actual)
- `debug_mode = true`
- `force_https = false` 
- `cors_allowed_origins = "*"`
- `jwt_access_token_lifetime_hours = 24`
- Logs mínimos

### Para Producción
- Cambiar `environment = "production"`
- `debug_mode = false`
- `force_https = true`
- Configurar dominio específico
- Habilitar CloudWatch

---

**Tip**: Todo está preconfigurado para testing. Solo ejecuta `terraform apply` y configura desde EC2 Console.

## Configuración Avanzada

### Certificado SSL con Route 53

```bash
# Solicitar certificado en ACM
DOMAIN="tu-dominio.com"
CERT_ARN=$(aws acm request-certificate \
  --domain-name $DOMAIN \
  --validation-method DNS \
  --query 'CertificateArn' \
  --output text)

# Agregar a terraform.tfvars
echo "ssl_certificate_arn = \"$CERT_ARN\"" >> terraform.tfvars

# Aplicar cambios
terraform apply
```

### Múltiples Entornos

```bash
# Desarrollo
cat > terraform-dev.tfvars << EOF
environment = "development"
debug_mode = true
force_https = false
instance_type = "t3.micro"
app_server_count = 1
jwt_access_token_lifetime_hours = 24
EOF

# Staging
cat > terraform-staging.tfvars << EOF
environment = "staging"
debug_mode = false
force_https = true
instance_type = "t3.small"
app_server_count = 2
JWT_access_token_lifetime_hours = 8
EOF

# Aplicar entorno específico
terraform apply -var-file="terraform-staging.tfvars"
```

## Gestión de Usuarios

Una vez desplegado, conéctate al servidor para configurar usuarios:

```bash
# Conectarse al primer servidor de aplicación
APP_IP=$(terraform output -raw app_server_1_public_ip)
ssh -i ~/.ssh/provesi-key.pem ubuntu@$APP_IP

# Configurar usuarios iniciales
cd /opt/apps/Inventario/ProvesiWMS
source ../venv/bin/activate
python setup_users.py

# Crear superusuario Django adicional
python manage.py createsuperuser
```

## Endpoints de la API

### Autenticación

```bash
# Login
curl -X POST "$ALB_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Respuesta
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q...",
  "user": {
    "id": 1,
    "username": "admin",
    "rol": "admin"
  }
}
```

### API Protegida

```bash
# Usar token de acceso
TOKEN="eyJ0eXAiOiJKV1Q..."

# Obtener pedidos (requiere autenticación)
curl -H "Authorization: Bearer $TOKEN" "$ALB_URL/pedidos/"

# Crear pedido (requiere rol 'gerente' o superior)
curl -X POST "$ALB_URL/pedidos/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"producto_id": 1, "cantidad": 10}'
```

## Monitoreo y Logs

### CloudWatch Logs

Los logs se envían automáticamente a CloudWatch si está habilitado:

- **Grupo**: `provesi-app-logs`
- **Streams**: 
  - `app-server-1-error`, `app-server-1-access`
  - `app-server-2-error`, `app-server-2-access`

```bash
# Ver logs desde AWS CLI
aws logs describe-log-groups --log-group-name-prefix provesi

# Tail logs en tiempo real
aws logs tail provesi-app-logs --follow
```

### Logs Locales

```bash
# Conectarse al servidor
ssh -i ~/.ssh/provesi-key.pem ubuntu@$APP_IP

# Ver logs de Gunicorn
tail -f /var/log/gunicorn/error.log
tail -f /var/log/gunicorn/access.log

# Ver logs de Supervisor
tail -f /var/log/supervisor/provesi-wms.log

# Estado de servicios
sudo systemctl status nginx supervisor
sudo supervisorctl status
```

## Escalamiento

### Horizontal (Más Servidores)

```bash
# Editar terraform.tfvars
sed -i 's/app_server_count = 2/app_server_count = 3/' terraform.tfvars

# Aplicar cambios
terraform apply
```

### Vertical (Más Recursos)

```bash
# Cambiar tipo de instancia
sed -i 's/instance_type = "t3.medium"/instance_type = "t3.large"/' terraform.tfvars

# Aplicar cambios (requiere reinicio)
terraform apply
```

## Costos Estimados

| Recurso | Tipo | Costo Mensual (us-east-1) |
|---------|------|---------------------------|
| 2x App Servers | t3.medium | ~$60/mes |
| 1x Database | t3.small | ~$30/mes |
| ALB | Standard | ~$23/mes |
| CloudWatch Logs | 1GB/mes | ~$2/mes |
| **Total Estimado** | | **~$115/mes** |

### Reducir Costos

1. **Reserved Instances**: 40% descuento
2. **Desarrollo**: t3.micro para todo (~$25/mes)
3. **Horarios**: Apagar fuera de horario laboral
4. **Spot Instances**: Para entornos no críticos

## Seguridad en Producción

### Lista de Verificación

- [ ] Cambiar `django_secret_key` por valor único
- [ ] Configurar `allowed_host` con dominio real
- [ ] Habilitar `force_https = true`
- [ ] Configurar certificado SSL (`ssl_certificate_arn`)
- [ ] Establecer `debug_mode = false`
- [ ] Configurar backup de base de datos
- [ ] Restringir SSH a IPs conocidas
- [ ] Implementar WAF en ALB
- [ ] Configurar alarmas CloudWatch

### Hardening Adicional

```bash
# Configurar backup automático
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier provesi-db \
  --db-cluster-snapshot-identifier provesi-backup-$(date +%Y%m%d)

# Configurar WAF
aws wafv2 create-web-acl \
  --name provesi-waf \
  --scope REGIONAL \
  --default-action Allow={}

# Restringir SSH por IP
# Editar main.tf, en aws_security_group.app:
# cidr_blocks = ["TU.IP.PUBLICA/32"]
```

## Troubleshooting

### Error de Autenticación JWT

```bash
# Verificar configuración JWT
echo "JWT_SECRET_KEY: $JWT_SECRET_KEY"
echo "JWT_ALGORITHM: $JWT_ALGORITHM"

# Verificar logs de autenticación
grep -i "jwt\|auth" /var/log/gunicorn/error.log
```

### Error de Base de Datos

```bash
# Test de conexión desde app server
pg_isready -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER

# Conectar manualmente
PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME

# Verificar migraciones
cd /opt/apps/Inventario/ProvesiWMS
source ../venv/bin/activate
python manage.py showmigrations
```

### ALB Health Check Failed

```bash
# Verificar que Django responde
curl -I http://localhost:8000/inventario/

# Verificar configuración de Gunicorn
sudo supervisorctl status provesi-wms

# Ver logs detallados
sudo journalctl -u supervisor -f
```

### CloudWatch Logs No Aparecen

```bash
# Verificar agente CloudWatch
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -m ec2 -a query-config

# Restart agente
sudo systemctl restart amazon-cloudwatch-agent
```

## Comandos Útiles

```bash
# Estado completo del deployment
./check_status.sh

# Reiniciar aplicación en todos los servidores
for ip in $(terraform output -json | jq -r '.app_server_public_ips.value[]'); do
  ssh -i ~/.ssh/provesi-key.pem ubuntu@$ip "sudo supervisorctl restart provesi-wms"
done

# Backup manual de base de datos
DB_IP=$(terraform output -raw database_private_ip)
ssh -i ~/.ssh/provesi-key.pem ubuntu@$(terraform output -raw app_server_1_public_ip) \
  "pg_dump -h $DB_IP -U inventario_user inventario_db > backup_$(date +%Y%m%d).sql"

# Destruir infraestructura
terraform destroy
```

## Soporte

- **Documentación Terraform**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Django Authentication**: https://docs.djangoproject.com/en/4.2/topics/auth/
- **JWT Documentation**: https://django-rest-framework-simplejwt.readthedocs.io/
- **AWS ALB**: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/

Para problemas específicos, revisar los archivos:
- `AUTHENTICATION.md` - Documentación completa de autenticación
- `deploy_aws.sh` - Script de deployment manual
- `setup_users.py` - Configuración de usuarios iniciales







## Deployment desde AWS CloudShell

### 1. Abrir CloudShell

1. Inicia sesión en AWS Console
2. Haz clic en el icono de CloudShell (>_) en la parte superior derecha
3. Espera a que se inicie (toma ~30 segundos)

### 2. Clonar el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario/ProvesiWMS/terraform

# Verificar versión de Terraform (debe ser >= 1.0)
terraform version
```

### 3. Crear Par de Claves SSH (si no lo tienes)

```bash
# Crear par de claves en AWS
aws ec2 create-key-pair \
  --key-name provesi-key \
  --query 'KeyMaterial' \
  --output text > provesi-key.pem

# Ajustar permisos
chmod 400 provesi-key.pem

# Mover a directorio seguro
mkdir -p ~/.ssh
mv provesi-key.pem ~/.ssh/
```

**NOTA:** Descarga esta clave a tu computadora si planeas conectarte por SSH desde fuera de CloudShell:

```bash
# En CloudShell, mostrar la clave para copiarla
cat ~/.ssh/provesi-key.pem
```

### 4. Configurar Variables

```bash
# Crear archivo de variables
cat > terraform.tfvars << 'EOF'
region = "us-east-1"
project_prefix = "provesi"
key_name = "provesi-key"
instance_type = "t2.small"
db_instance_type = "t2.micro"
db_password = "ChangeMe123!"
EOF
```

**IMPORTANTE:** Cambia `db_password` por una contraseña segura.

### 5. Inicializar Terraform

```bash
terraform init
```

### 6. Revisar Plan

```bash
terraform plan
```

Revisa los recursos que se crearán:
- 3 Security Groups
- 2 App Servers (t2.small)
- 1 Database Server (t2.micro)
- 1 Application Load Balancer
- 1 Target Group

### 7. Aplicar Infraestructura

```bash
terraform apply
```

Escribe `yes` cuando se solicite confirmación.

**Tiempo estimado:** 5-10 minutos

### 8. Guardar Outputs

```bash
# Guardar outputs en un archivo para referencia
terraform output > deployment_info.txt
cat deployment_info.txt
```

### 9. Probar la Aplicación

```bash
# Obtener URL del Load Balancer
ALB_URL=$(terraform output -raw alb_url)
echo "Aplicación disponible en: $ALB_URL"

# Probar endpoint
curl -I $ALB_URL
```

### 10. Mantener CloudShell Activo

CloudShell se cierra después de ~20 minutos de inactividad. Para mantener el estado de Terraform:

```bash
# Los archivos en ~/Inventario se persisten automáticamente
# CloudShell mantiene terraform.tfstate entre sesiones
```

## Deployment desde tu Computadora Local

### 1. Configurar Variables (Opcional)

Copia el archivo de ejemplo y personaliza los valores:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edita `terraform.tfvars`:

```hcl
region = "us-east-1"
project_prefix = "provesi"
instance_type = "t2.small"
db_instance_type = "t2.micro"
db_password = "tu_password_seguro"
```

### 2. Inicializar Terraform

```bash
terraform init
```

### 3. Revisar Plan de Ejecución

```bash
terraform plan
```

Esto mostrará todos los recursos que se crearán.

### 4. Desplegar Infraestructura

```bash
terraform apply
```

Escribe `yes` cuando se solicite confirmación.

El despliegue toma aproximadamente 5-10 minutos.

## Outputs

Después del despliegue, Terraform mostrará:

```
Outputs:

alb_dns_name = "provesi-alb-123456789.us-east-1.elb.amazonaws.com"
alb_url = "http://provesi-alb-123456789.us-east-1.elb.amazonaws.com/inventario/"
app_server_1_public_ip = "54.123.45.67"
app_server_2_public_ip = "54.123.45.68"
database_private_ip = "10.0.10.123"
ssh_app_server_1 = "ssh ubuntu@54.123.45.67"
ssh_app_server_2 = "ssh ubuntu@54.123.45.68"
```

## Acceder a la Aplicación

Una vez desplegado, accede a la aplicación:

```
http://[ALB_DNS_NAME]/inventario/
```

El ALB distribuirá automáticamente el tráfico entre ambos servidores.

## Conectarse a los Servidores

### Servidores de Aplicación

```bash
ssh -i tu-llave.pem ubuntu@[APP_SERVER_IP]
```

Ver logs de la aplicación:

```bash
sudo journalctl -u provesi-wms -f
```

Reiniciar servicio:

```bash
sudo systemctl restart provesi-wms
```

### Base de Datos

La base de datos está en una subnet privada (sin IP pública). Para acceder:

1. Conéctate a un servidor de aplicación
2. Desde ahí, conéctate a la base de datos:

```bash
psql -h [DATABASE_PRIVATE_IP] -U inventario_user -d inventario_db
```

## Configuración de Django para PostgreSQL

El user_data script ya configura las variables de entorno, pero si necesitas actualizar `settings.py`:

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'inventario_db'),
        'USER': os.environ.get('DATABASE_USER', 'inventario_user'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'inventario2024'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

ALLOWED_HOSTS = ['*']  # En producción, limitar a dominios específicos
```

## Pruebas de Carga

Para ejecutar pruebas de carga contra el ALB:

```bash
# Actualizar config_entornos.py en tu máquina local
BASE_URL = "http://[ALB_DNS_NAME]"

# Ejecutar Locust
./tests/run_load_tests.sh objective
```

## Escalamiento

### Agregar más servidores de aplicación

Edita `main.tf` y cambia el count:

```hcl
resource "aws_instance" "app_server" {
  count = 3  # Cambiar de 2 a 3 o más
  ...
}
```

Luego:

```bash
terraform apply
```

### Cambiar tipo de instancia

En `terraform.tfvars`:

```hcl
instance_type = "t2.medium"  # Más potente
db_instance_type = "t2.small"
```

## Costos Estimados

Costos mensuales aproximados (región us-east-1):

- 2x t2.small (app servers): ~$33/mes ($16.50 cada una)
- 1x t2.micro (database): ~$8.50/mes
- ALB: ~$23/mes (base + datos transferidos)
- Transferencia de datos: Variable según uso

**Total estimado: ~$65-80/mes**

Reducir costos:
- Usar Reserved Instances (descuento ~40%)
- Apagar instancias fuera de horario laboral
- Usar t2.micro para todos los servidores en dev/testing

## Conectarse desde CloudShell

Si desplegaste desde CloudShell, puedes conectarte a los servidores directamente:

```bash
# Conectarse a App Server 1
APP_IP=$(terraform output -raw app_server_1_public_ip)
ssh -i ~/.ssh/provesi-key.pem ubuntu@$APP_IP

# Conectarse a App Server 2
APP_IP=$(terraform output -raw app_server_2_public_ip)
ssh -i ~/.ssh/provesi-key.pem ubuntu@$APP_IP

# Ver logs de la aplicación
sudo journalctl -u provesi-wms -f

# Reiniciar servicio
sudo systemctl restart provesi-wms
```

## Destruir Infraestructura

Para eliminar todos los recursos y evitar costos:

```bash
terraform destroy
```

Escribe `yes` cuando se solicite confirmación.

**ADVERTENCIA**: Esto eliminará TODOS los datos de la base de datos.

### Limpiar CloudShell (Opcional)

```bash
# Eliminar archivos del repositorio
cd ~
rm -rf Inventario

# Eliminar par de claves de AWS
aws ec2 delete-key-pair --key-name provesi-key
rm -f ~/.ssh/provesi-key.pem
```

## Troubleshooting

### CloudShell se quedó sin espacio

CloudShell tiene 1GB de almacenamiento persistente. Si te quedas sin espacio:

```bash
# Ver uso de espacio
df -h

# Limpiar cache de Terraform
rm -rf .terraform/
terraform init

# Limpiar archivos temporales
rm -rf /tmp/*
```

### CloudShell perdió la sesión

Si CloudShell se reinició, tus archivos se mantienen pero necesitas:

```bash
cd ~/Inventario/ProvesiWMS/terraform
terraform init
terraform plan  # Verificar que el estado está intacto
```

### No puedo acceder por SSH desde fuera de CloudShell

Si desplegaste desde CloudShell y quieres conectarte desde tu computadora:

1. Copia la clave privada:
   ```bash
   # En CloudShell
   cat ~/.ssh/provesi-key.pem
   ```

2. En tu computadora:
   ```bash
   # Pega el contenido en un archivo
   nano provesi-key.pem
   # Pega el contenido y guarda
   chmod 400 provesi-key.pem
   
   # Conéctate
   ssh -i provesi-key.pem ubuntu@[APP_SERVER_IP]
   ```

### Health Check fallando

Verifica que Django responda en `/inventario/`:

```bash
curl http://[APP_SERVER_IP]:8000/inventario/
```

Si falla, revisa logs:

```bash
sudo journalctl -u provesi-wms -n 50
```

### No se puede conectar al ALB

1. Verifica que el ALB esté "active":
   ```bash
   aws elbv2 describe-load-balancers
   ```

2. Verifica targets:
   ```bash
   aws elbv2 describe-target-health --target-group-arn [TG_ARN]
   ```

### Error en migraciones de base de datos

Conectarse a app-server-1 y ejecutar manualmente:

```bash
cd /opt/apps/Inventario/ProvesiWMS
source ../venv/bin/activate
python manage.py migrate
```

### Timeout en user_data

Los scripts user_data pueden tardar. Para ver el progreso:

```bash
sudo tail -f /var/log/cloud-init-output.log
```

## Seguridad en Producción

Antes de usar en producción:

1. **Cambiar SECRET_KEY** en settings.py
2. **Configurar ALLOWED_HOSTS** con dominios específicos
3. **Habilitar HTTPS** en el ALB (requiere certificado SSL)
4. **Restringir SSH** solo a IPs conocidas
5. **Habilitar DEBUG = False**
6. **Configurar backups** de base de datos
7. **Implementar WAF** en el ALB

## Archivos

- `main.tf` - Definición completa de infraestructura
- `variables.tf` - Variables configurables
- `outputs.tf` - Outputs después del despliegue
- `terraform.tfvars.example` - Ejemplo de configuración
- `README.md` - Este archivo

## Soporte

Para problemas o preguntas, consulta la documentación de Terraform AWS:
https://registry.terraform.io/providers/hashicorp/aws/latest/docs
