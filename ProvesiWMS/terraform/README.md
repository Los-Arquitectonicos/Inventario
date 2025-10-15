# Terraform Infrastructure as Code - ProvesiWMS

Este directorio contiene la infraestructura como código (IaC) para desplegar ProvesiWMS en AWS.

## Arquitectura

La infraestructura incluye:

- **VPC por defecto de AWS** (usa la infraestructura existente)
- **Application Load Balancer (ALB)** para distribuir tráfico
- **2 instancias EC2** con Django/Gunicorn
- **1 instancia EC2** con PostgreSQL
- **Security Groups** para controlar acceso entre componentes

```
                    Internet
                       |
                  [ALB - Port 80]
                       |
        +--------------+---------------+
        |                              |
   [App Server 1]               [App Server 2]
   Django:8000                  Django:8000
        |                              |
        +-------------+----------------+
                      |
                [PostgreSQL]
                  Port 5432
```

## Prerequisitos







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
