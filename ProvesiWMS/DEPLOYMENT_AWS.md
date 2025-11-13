# Deployment ProvesiWMS en AWS - Guía Simple

Esta guía te permite desplegar ProvesiWMS en AWS usando solo el Dashboard de AWS CloudShell y la consola EC2.

## Paso 1: Acceder a AWS CloudShell

1. **Inicia sesión** en AWS Console: https://aws.amazon.com/console/
2. **Busca "CloudShell"** en la barra de búsqueda superior
3. **Haz clic** en el icono CloudShell (>_) en la parte superior derecha
4. **Espera** aproximadamente 30 segundos a que se inicie

## Paso 2: Clonar el Proyecto

```bash
# Clonar repositorio
git clone https://github.com/Los-Arquitectonicos/Inventario.git

# Navegar al directorio terraform
cd Inventario/ProvesiWMS/terraform
```

## Paso 3: Desplegar Infraestructura

```bash
# Inicializar Terraform
terraform init

#Planear configuración
terraform plan

# Aplicar configuración (crear recursos)
terraform apply
```

Escribe **"yes"** cuando te pregunte si quieres continuar.

⏱️ **Tiempo estimado**: 10-15 minutos

## Paso 4: Obtener IPs de las Instancias

```bash
# Ver información de las instancias creadas
terraform output
```

Anota las IPs públicas de `app_server_1_public_ip` y `app_server_2_public_ip`.

## Paso 5: Configurar Servidores desde la Consola EC2

### 5.1 Acceder a la Consola EC2

1. **Ve a EC2** en AWS Console: https://console.aws.amazon.com/ec2/
2. **Haz clic** en "Instances" en el menú lateral
3. **Busca las instancias** con nombres `provesi-app-server-1` y `provesi-app-server-2`

### 5.2 Conectar a la Primera Instancia

1. **Selecciona** `provesi-app-server-1`
2. **Haz clic** en "Connect" (botón superior)
3. **Selecciona** la pestaña "EC2 Instance Connect"
4. **Deja** el username como `ubuntu`
5. **Haz clic** en "Connect"

### 5.3 Configurar Aplicación en el Servidor 1

**Django se configura automáticamente durante el despliegue de Terraform y se ejecuta como servicio systemd.**

```bash
# Verificar que Django está funcionando
./check-status.sh

# Ver logs en tiempo real
./logs-django.sh

# Gestionar el servicio
./restart-django.sh  # Reiniciar
./stop-django.sh     # Detener  
./start-django.sh    # Iniciar
./help-django.sh     # Ver ayuda completa
```

**⚠️ IMPORTANTE**: NO ejecutes `python3 manage.py runserver` manualmente. Django ya está corriendo como servicio automático.

### 5.4 Configurar el Servidor 2

**El segundo servidor también se configura automáticamente.** Solo verifica que esté funcionando:

```bash
# En el Servidor 2, verificar estado
./check-status.sh

# Si necesitas gestionar el servicio
./restart-django.sh
```

## Paso 6: Probar la Aplicación

```bash
# En CloudShell, obtener URL del Load Balancer
terraform output alb_url
```

Abre esa URL en tu navegador. Deberías ver la aplicación funcionando.

## Usuarios por Defecto

La aplicación viene con estos usuarios preconfigurados:

- **admin/admin123** (Administrador)
- **gerente/gerente123** (Gerente)
- **supervisor/supervisor123** (Supervisor)  
- **empleado/empleado123** (Empleado)

## Endpoints de Autenticación

```bash
# Login
POST /inventario/auth/login/
Body: {"username": "admin", "password": "admin123"}

# Usar la aplicación
GET /inventario/
```

## Comandos Útiles para la Consola EC2

### Verificar Estado del Servidor

```bash
# Ver si el servidor Django está corriendo
ps aux | grep manage.py

# Ver logs de la aplicación
tail -f /var/log/django/app.log
```

### Reinstalar Django y Dependencias

```bash
# Si encuentras errores de módulos no encontrados, instala todo manualmente
sudo apt update
sudo apt install -y python3-pip python3-dev libpq-dev build-essential postgresql-client
sudo pip3 install --break-system-packages django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers

# Verificar instalación
python3 -c "import django; print('Django version:', django.get_version())"
```

### Reinstalar Django y Dependencias

```bash
# Si encuentras errores de módulos no encontrados, instala todo manualmente
sudo apt update
sudo apt install -y python3-pip python3-dev libpq-dev build-essential postgresql-client
sudo pip3 install django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers

# Verificar instalación
python3 -c "import django; print('Django version:', django.get_version())"
```

### Reiniciar Servidor Django

```bash
# Detener servidor actual
sudo pkill -f "manage.py runserver" || pkill -f "python3.*runserver"

# Verificar que Django está instalado
python3 -c "import django; print('Django OK')" || sudo pip3 install --break-system-packages django==4.2.24 psycopg2-binary

# Ir al directorio correcto
cd ~/Inventario/ProvesiWMS

# Cargar variables de entorno si existen
source /etc/environment 2>/dev/null || echo "Configurar variables manualmente"

# Iniciar servidor
python3 manage.py runserver 0.0.0.0:8080
```

### Configuración Completa Manual (si falló el script automático)

```bash
# 1. Clonar repositorio si no existe
cd ~
if [ ! -d "Inventario" ]; then
    git clone https://github.com/Los-Arquitectonicos/Inventario.git
fi
cd Inventario
git checkout Sprint3V2

# 2. Instalar dependencias
sudo apt update
sudo apt install -y python3-pip python3-dev libpq-dev build-essential postgresql-client
sudo pip3 install --break-system-packages django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers

# 3. Obtener IP de base de datos (desde CloudShell)
# terraform output database_private_ip

# 4. Configurar variables de entorno (reemplaza IP_DE_TU_BD con la IP real)
export DATABASE_HOST="IP_DE_TU_BD"  # Ejemplo: 172.31.45.123
export DATABASE_NAME="provesi_wms"
export DATABASE_USER="provesi_user" 
export DATABASE_PASSWORD="provesi_password_2024"
export SECRET_KEY="django-insecure-test-key-2024"
export DEBUG="True"

# 5. Aplicar configuración (solo en el primer servidor)
cd ProvesiWMS
python3 manage.py migrate
python3 setup_users.py

# 6. Iniciar servidor
python3 manage.py runserver 0.0.0.0:8080
```

### Verificar Variables de Entorno

```bash
# Ver configuración de la aplicación
env | grep -E "DATABASE_|SECRET_KEY|DEBUG"
```

## Limpieza (Eliminar Todo)

⚠️ **CUIDADO**: Esto eliminará toda la infraestructura y datos.

```bash
# En CloudShell, ir al directorio terraform
cd Inventario/ProvesiWMS/terraform

# Eliminar toda la infraestructura
terraform destroy
```

Escribe **"yes"** para confirmar.

## Costos Estimados

- **2x t3.medium**: ~$60/mes
- **1x t3.small (DB)**: ~$30/mes  
- **Load Balancer**: ~$23/mes
- **Total**: ~$113/mes

## Troubleshooting

### Error: "externally-managed-environment"

Si obtienes este error al instalar paquetes con pip, es porque Ubuntu 24.04 protege el entorno Python del sistema. Soluciones:

**Opción A: Usar --break-system-packages (Recomendado para AWS)**

```bash
sudo pip3 install --break-system-packages django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers
```

**Opción B: Usar entorno virtual**

```bash
# Crear entorno virtual
python3 -m venv ~/venv-provesi
source ~/venv-provesi/bin/activate

# Instalar dependencias en el entorno virtual
pip install django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers

# Recordar activar el entorno cada vez que uses Django
source ~/venv-provesi/bin/activate
cd ~/Inventario/ProvesiWMS
python manage.py runserver 0.0.0.0:8000
```

### Error: "No module named 'django'"

Si obtienes este error, significa que Django no se instaló automáticamente. Solución:

```bash
# Instalar Django y todas las dependencias necesarias
sudo apt update
sudo apt install -y python3-pip python3-dev libpq-dev build-essential
sudo pip3 install django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers

# Verificar que Django se instaló correctamente
python3 -c "import django; print('Django version:', django.get_version())"

# Si todo está bien, continuar con la configuración
cd ~/Inventario/ProvesiWMS
python3 manage.py migrate
python3 setup_users.py
python3 manage.py runserver 0.0.0.0:8080
```

### Error: Repositorio no clonado

Si no existe el directorio `~/Inventario`, clónalo manualmente:

```bash
cd ~
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario
git checkout Sprint3V2
cd ProvesiWMS
```

### Error: Variables de entorno no configuradas

Si las variables de base de datos no están configuradas automáticamente, configúralas manualmente:

```bash
# Configurar variables de entorno temporalmente
export DATABASE_HOST="ip-de-tu-base-de-datos"
export DATABASE_NAME="provesi_wms"
export DATABASE_USER="provesi_user"
export DATABASE_PASSWORD="provesi_password_2024"
export SECRET_KEY="tu-secret-key-aqui"
export DEBUG="True"

# Para hacerlas permanentes
echo 'export DATABASE_HOST="ip-de-tu-base-de-datos"' >> ~/.bashrc
echo 'export DATABASE_NAME="provesi_wms"' >> ~/.bashrc
echo 'export DATABASE_USER="provesi_user"' >> ~/.bashrc
echo 'export DATABASE_PASSWORD="provesi_password_2024"' >> ~/.bashrc
echo 'export SECRET_KEY="django-insecure-test-key-2024"' >> ~/.bashrc
echo 'export DEBUG="True"' >> ~/.bashrc
source ~/.bashrc
```

### Error: No se puede conectar desde EC2 Console
1. **Verifica** que la instancia esté en estado "running"
2. **Espera** 2-3 minutos después del deployment
3. **Prueba** refrescar la página de la instancia

### Error: Servidor Django no responde
```bash
# En la consola de la instancia, verificar que esté corriendo
ps aux | grep manage.py

# Si no está corriendo, iniciarlo
cd /opt/apps/Inventario/ProvesiWMS
source ../venv/bin/activate
sudo python3 manage.py runserver 0.0.0.0:8080
```

### Error: Variables de entorno no configuradas
Las variables están preconfiguradas en los archivos Terraform para entorno de pruebas. Si hay problemas:

```bash
# Verificar variables
env | grep DATABASE_HOST
env | grep SECRET_KEY
```

---

**¡Listo!** Tu aplicación ProvesiWMS está corriendo en AWS con autenticación JWT, sin necesidad de configurar SSH.

## Usuarios por Defecto

La aplicación viene con estos usuarios preconfigurados:

- **admin/admin123** (Administrador)
- **gerente/gerente123** (Gerente)
- **supervisor/supervisor123** (Supervisor)  
- **empleado/empleado123** (Empleado)

## Endpoints de Autenticación

```bash
# Login
POST /inventario/auth/login/
Body: {"username": "admin", "password": "admin123"}

# Usar la aplicación
GET /inventario/
```

## Comandos Útiles

### Verificar Estado de los Servidores

```bash
# Ver si el servidor Django está corriendo
ps aux | grep manage.py

# Ver logs en tiempo real
tail -f /var/log/gunicorn/error.log
```

### Reiniciar Servidor Django

```bash
# Detener servidor actual
sudo pkill -f "manage.py runserver"

# Iniciar nuevamente
sudo python3 manage.py runserver 0.0.0.0:8080
```

## Limpieza (Eliminar Todo)

⚠️ **CUIDADO**: Esto eliminará toda la infraestructura y datos.

```bash
# En CloudShell, ir al directorio terraform
cd Inventario/ProvesiWMS/terraform

# Eliminar toda la infraestructura
terraform destroy
```

Escribe **"yes"** para confirmar.

## Costos Estimados

- **2x t3.medium**: ~$60/mes
- **1x t3.small (DB)**: ~$30/mes  
- **Load Balancer**: ~$23/mes
- **Total**: ~$113/mes

## Troubleshooting

### Error: No se puede conectar por SSH
```bash
# Verificar que la clave tenga permisos correctos
chmod 400 provesi-key.pem
```

### Error: Servidor Django no responde
```bash
# Verificar que el servidor esté corriendo
ps aux | grep manage.py

# Si no está corriendo, iniciarlo
sudo python3 manage.py runserver 0.0.0.0:8080
```

### Error: Base de datos no conecta
```bash
# Verificar variables de entorno
env | grep DATABASE
```

---

**¡Listo!** Tu aplicación ProvesiWMS está corriendo en AWS con autenticación JWT y **gestión automática permanente** mediante systemd.

## 🔧 Solución Permanente Implementada

### ✅ Django como Servicio Automático
- Django se **inicia automáticamente** al reiniciar el servidor
- **Puerto 8000** reservado para el servicio systemd  
- **NO necesitas** ejecutar `python3 manage.py runserver` manualmente
- **Reinicio automático** en caso de fallos

### ✅ Scripts de Gestión Incluidos
Cada servidor tiene scripts preinstalados para gestión fácil:

```bash
./check-status.sh    # Estado completo del sistema
./restart-django.sh  # Reiniciar Django
./stop-django.sh     # Detener Django
./start-django.sh    # Iniciar Django  
./logs-django.sh     # Ver logs en tiempo real
./help-django.sh     # Ayuda completa
```

### ✅ Configuración Robusta
- **Reinicio automático** si Django falla
- **Variables de entorno** preconfiguradas
- **Base de datos** conectada automáticamente
- **Load Balancer** configurado en puerto 80
- **Logs centralizados** con systemd

### ✅ Acceso Correcto
- **Load Balancer URL**: `terraform output alb_url`
- **Puerto externo**: 80 (HTTP)
- **Puerto interno**: 8000 (reservado para systemd)
- **Nunca acceder directamente** al puerto 8000 desde fuera

### ✅ Monitoreo y Troubleshooting
```bash
# Ver estado
sudo systemctl status provesi-wms

# Ver logs en tiempo real  
sudo journalctl -u provesi-wms -f

# Verificar conectividad
curl http://localhost:8000/inventario/
```