# 🚀 Guía de Despliegue con Terraform

## 📋 Desplegar ProvesiWMS en AWS usando Terraform

Esta guía te llevará desde cero hasta tener tu aplicación Django corriendo en AWS con un Application Load Balancer.

---

## 🎯 Arquitectura

```
Internet → ALB → [EC2-App-1, EC2-App-2] → EC2-Database
```

- **Application Load Balancer**: Distribuye tráfico HTTP
- **2 Instancias EC2**: Django + Gunicorn + Auth0
- **1 Instancia PostgreSQL**: Base de datos
- **Security Groups**: Control de acceso

---

## 📋 Prerrequisitos

### Herramientas Necesarias

```bash
# Verificar instalación
terraform --version    # v1.5.x o superior
aws --version          # AWS CLI v2
```

### Instalar si es necesario

```bash
# En macOS
brew install terraform awscli

# En CloudShell/Ubuntu
curl -fsSL https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip -o terraform.zip
unzip terraform.zip && sudo mv terraform /usr/local/bin/
```

### Configurar AWS

```bash
aws configure
# Ingresar: Access Key, Secret Key, region (us-east-1), formato (json)

# Verificar
aws sts get-caller-identity
```

---

## 🚀 Paso 1: Inicializar Infraestructura

### 1.1 Navegar al CloudShell de AWS

```bash
# Clonar el repositorio
git clone https://github.com/Los-Arquitectonicos/Inventario.git

# Ir al directorio del proyecto
cd Inventario/ProvesiWMS/terraform

# Cambiar a la rama pertinente
git checkout Sprint3

# Hacer pull de los cambios
git fetch
git pull

# Verificar archivos
ls -la
# Deberías ver: main.tf, variables.tf, terraform.tfvars
```

### 1.2 Inicializar Terraform

```bash
# Descargar providers necesarios
terraform init

# ✅ Deberías ver: "Terraform has been successfully initialized!"
```

### 1.3 Revisar y Aplicar

```bash
# Ver qué se va a crear
terraform plan

# Crear infraestructura (toma 5-10 minutos)
terraform apply

# Escribir "yes" cuando lo solicite
```

---

## 📦 Paso 2: Verificar Instalación

### 2.1 Obtener URLs

```bash
# Ver información de lo creado
terraform output

# Ejemplo:
# alb_dns_name = "provesi-alb-1234567890.us-east-1.elb.amazonaws.com"
# app_server_ips = ["54.123.45.67", "34.567.89.12"]
```

### 2.2 Verificar Estado del Sistema

```bash
# Guardar URL del balanceador
ALB_URL=$(terraform output -raw alb_dns_name)
echo "URL: http://$ALB_URL"

# Esperar 2-3 minutos para que las instancias terminen de configurarse
# Luego probar:
curl http://$ALB_URL/inventario/
# ✅ Debería devolver código 200
```

---

## 🖥️ Paso 3: Inicializar Servidor en las Instancias EC2

### 3.1 Conectarse a las Instancias

1. Ir a EC2 Dashboard → Instances
2. Seleccionar instancia `provesi-app-server-1`
3. Click "Connect" → "Session Manager" → "Connect"


### 3.2 Verificar Estado del Sistema

```bash
# Una vez conectado a la instancia EC2:

# Verificar que el script de instalación terminó
sudo tail -f /var/log/cloud-init-output.log
# Presiona Ctrl+C cuando veas "Cloud-init finished"

# Verificar estado del servicio Django
sudo systemctl status provesi-wms
```

### 3.3 Inicializar el Servidor Manualmente

Si el servicio no está corriendo automáticamente:

```bash
# Ir al directorio del proyecto
cd /opt/apps/Inventario/ProvesiWMS

# Activar entorno virtual
source ../venv/bin/activate

# Verificar que Django funciona
python3 manage.py check

# Aplicar migraciones (solo en la primera instancia)
python3 manage.py migrate

# Recopilar archivos estáticos
python3 manage.py collectstatic --noinput

# Iniciar servidor Django
python3 manage.py runserver 0.0.0.0:8000

# El servidor debería mostrar:
# "Starting development server at http://0.0.0.0:8000/"
# "Quit the server with CONTROL-C."
```

### 3.4 Verificar Logs del Servidor

```bash
# Si usas runserver, los logs aparecerán directamente en la terminal
# Para ejecutar en background, usa:
nohup python3 manage.py runserver 0.0.0.0:8000 > /var/log/django.log 2>&1 &

# Ver logs del servidor
tail -f /var/log/django.log

# Ver logs de Django (si están configurados)
tail -f /var/log/provesi-wms/error.log
```

### 3.5 Probar Servidor Localmente

```bash
# Probar desde la misma instancia EC2
curl localhost:8000/inventario/

# Debería devolver código 200
```

**Repetir estos pasos en la segunda instancia:** `provesi-app-server-2`

---

## 🌐 Paso 4: Probar la Aplicación

### 4.1 Health Check

```bash
# Verificar que el sistema responde
curl -v http://$ALB_URL/inventario/

# ✅ Respuesta esperada: HTTP/1.1 200 OK
```

### 4.2 Probar API

```bash
# Probar endpoint sin autenticación
curl http://$ALB_URL/api/productos/

# ✅ Respuesta esperada: 401 Unauthorized (correcto, necesita auth)
```

### 4.3 URLs Disponibles

Una vez funcionando, puedes acceder a:

```bash
# Frontend principal
http://$ALB_URL/

# API
http://$ALB_URL/api/

# Admin de Django  
http://$ALB_URL/admin/

# Health check
http://$ALB_URL/inventario/
```

---

## �️ Troubleshooting

### Problema: Terraform falla

```bash
# Verificar credenciales AWS
aws sts get-caller-identity

# Re-inicializar si es necesario
terraform init
```

### Problema: ALB devuelve 503

```bash
# Esperar 3-5 minutos adicionales para que terminen de instalarse las dependencias

# Verificar estado de target group
aws elbv2 describe-target-health --target-group-arn $(terraform output -raw target_group_arn)
```

### Problema: Conectar y configurar instancia EC2

```bash
# Obtener IP de instancia
terraform output app_server_ips

# Conectar vía AWS Console:
# 1. EC2 Dashboard → Instances
# 2. Seleccionar "provesi-app-server-1"
# 3. Connect → Session Manager → Connect

# Una vez conectado, ir al proyecto:
cd /opt/apps/Inventario/ProvesiWMS
source ../venv/bin/activate

# Verificar Django
python3 manage.py check

# Iniciar servidor
python3 manage.py runserver 0.0.0.0:8000

# Para ejecutar en background:
nohup python3 manage.py runserver 0.0.0.0:8000 > /var/log/django.log 2>&1 &
```

---

## 🧹 Limpieza

### Destruir todo

```bash
# ⚠️ CUIDADO: Elimina toda la infraestructura
terraform destroy

# Confirmar con: yes
```

---

## ✅ Checklist

- [ ] AWS configurado
- [ ] `terraform init` exitoso  
- [ ] `terraform apply` completado
- [ ] Health check devuelve 200
- [ ] API responde (401 sin auth es correcto)

**🎉 ¡Tu aplicación está corriendo en AWS!**