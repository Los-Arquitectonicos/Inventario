# Guía de Despliegue en AWS CloudShell

## Preparación y Despliegue de la Infraestructura ProvesiWMS

### 1. Acceso a AWS CloudShell

1. **Inicia sesión en la Consola de AWS**
   - Ve a [https://console.aws.amazon.com](https://console.aws.amazon.com)
   - Inicia sesión con tus credenciales

2. **Abre CloudShell**
   - En la barra superior, busca el ícono de CloudShell (>_)
   - O ve a Servicios → CloudShell
   - Espera a que se inicialice (puede tomar 1-2 minutos la primera vez)

### 2. Configuración Inicial en CloudShell

```bash
# 1. Clonar el repositorio
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario

# 2. Cambiar a la rama de notificaciones
git checkout notificaciones

# 3. Navegar al directorio de Terraform
cd terraform

# 4. Verificar archivos necesarios
ls -la
```

### 3. Instalación de Terraform en CloudShell

```bash
# 1. Descargar e instalar Terraform
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# 2. Verificar instalación
terraform version

# 3. Limpiar archivos temporales
rm terraform_1.6.6_linux_amd64.zip
```

### 4. Configuración de Variables de Entorno

```bash
# 1. Copiar archivo de ejemplo si no existe
cp terraform.tfvars.example terraform.tfvars

# 2. Editar variables (opcional)
# nano terraform.tfvars
# Puedes usar los valores por defecto o modificar según necesidades
```

### 5. Despliegue de la Infraestructura

```bash
# 1. Inicializar Terraform
terraform init

# 2. Validar configuración
terraform validate

# 3. Ver el plan de despliegue
terraform plan

# 4. Aplicar la infraestructura (CONFIRMACIÓN REQUERIDA)
terraform apply
# Escribir 'yes' cuando se solicite confirmación
```

### 6. Verificación del Despliegue

```bash
# 1. Verificar outputs importantes
terraform output

# 2. Verificar estado de la infraestructura
terraform state list

# 3. Obtener información específica
terraform output kong_gateway_ip
terraform output application_load_balancer_dns
```

### 7. Despliegue de Kong Gateway (Automatizado)

```bash
# El script está incluido y se ejecuta automáticamente
# Pero puedes verificar manualmente:
chmod +x deploy_kong_gateway.sh
./deploy_kong_gateway.sh
```

### 8. Pruebas de Conectividad

```bash
# 1. Obtener las IPs/DNS
ALB_DNS=$(terraform output -raw application_load_balancer_dns)
KONG_IP=$(terraform output -raw kong_gateway_ip)

# 2. Probar Kong Gateway
curl -v http://$KONG_IP:8000/health

# 3. Probar a través del ALB
curl -v http://$ALB_DNS/api/health

# 4. Probar Django API
curl -v http://$ALB_DNS/api/productos/

# 5. Probar Notifications API
curl -v http://$ALB_DNS/notifications/health
```

## Comandos de Limpieza (Cuando sea necesario)

### Destruir la Infraestructura

```bash
# ⚠️ CUIDADO: Esto eliminará TODA la infraestructura
terraform destroy
# Escribir 'yes' cuando se solicite confirmación
```

### Limpiar Estado Local

```bash
# Solo si hay problemas con el estado
rm -rf .terraform
rm terraform.tfstate*
terraform init
```

## Estructura de la Infraestructura Desplegada

Después del despliegue tendrás:

### 1. **Application Load Balancer (ALB)**
   - Puerto 80 (HTTP) y 443 (HTTPS)
   - Distribución de tráfico entre servicios

### 2. **Kong API Gateway**
   - Instancia EC2 t3.small
   - Puerto 8000 (Admin), 8001 (API)
   - Configuración declarativa

### 3. **Django API**
   - 2 instancias EC2 t3.medium
   - Puerto 8000
   - Auto Scaling configurado

### 4. **Notifications Service**
   - 1 instancia EC2 t3.small
   - Puerto 3001
   - MongoDB integrado

### 5. **Base de Datos PostgreSQL**
   - RDS t3.small
   - Backup automático configurado

### 6. **Grupos de Seguridad**
   - ALB: 80, 443
   - Kong: 8000, 8001
   - Django: 8000
   - Notifications: 3001
   - Database: 5432

## Troubleshooting

### Problema: Terraform no instalado
```bash
# Repetir la instalación de Terraform del paso 3
```

### Problema: Permisos insuficientes
```bash
# Verificar que tu usuario IAM tenga permisos de:
# EC2FullAccess, RDSFullAccess, ELBFullAccess, VPCFullAccess
```

### Problema: Estado inconsistente
```bash
terraform refresh
terraform plan
```

### Problema: Kong no responde
```bash
# Conectar por SSH a la instancia Kong
KONG_IP=$(terraform output -raw kong_gateway_ip)
ssh -i ~/.ssh/your-key.pem ubuntu@$KONG_IP

# Verificar estado de Kong
sudo systemctl status kong
sudo journalctl -u kong -f
```

## Próximos Pasos

1. **Configurar DNS personalizado** (opcional)
2. **Habilitar HTTPS con certificado SSL**
3. **Configurar JWT Authentication en Kong**
4. **Agregar monitoreo con CloudWatch**
5. **Configurar backup automático**

## Contactos de Emergencia

- **Documentación de Terraform**: terraform.io/docs
- **Documentación de Kong**: docs.konghq.com
- **AWS CloudShell**: docs.aws.amazon.com/cloudshell