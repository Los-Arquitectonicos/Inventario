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

## Paso 5: Iniciar Django en los Servidores

### 5.1 Acceder a la Primera Instancia

1. **Selecciona** `provesi-app-server-1`
2. **Haz clic** en "Connect" (botón superior)
3. **Selecciona** la pestaña "EC2 Instance Connect"
4. **Deja** el username como `ubuntu`
5. **Haz clic** en "Connect"

### 5.2 Iniciar Django en el Servidor 1

```bash
# Ir al directorio de la aplicación
cd ~/Inventario/ProvesiWMS

# Verificar que Django está instalado
python3 -c "import django; print('Django version:', django.get_version())"

# Verificar variables de entorno
echo "DATABASE_HOST: $DATABASE_HOST"
echo "DATABASE_NAME: $DATABASE_NAME"

# Iniciar servidor Django
python3 manage.py runserver 0.0.0.0:8000
```

### 5.3 Iniciar Django en el Servidor 2

**Repite el proceso** para `provesi-app-server-2`:

```bash
# Ir al directorio de la aplicación
cd ~/Inventario/ProvesiWMS

# Verificar que Django está instalado
python3 -c "import django; print('Django version:', django.get_version())"

# Iniciar servidor Django en BACKGROUND PERMANENTE (NO hacer migraciones en el segundo servidor)
# IMPORTANTE: Django debe correr en background para que el Load Balancer funcione
nohup python3 manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &

# Verificar que el proceso está corriendo
ps aux | grep runserver

# Obtener el PID para poder controlarlo después
echo "Django PID: $(pgrep -f runserver)"
```

### 5.4 Verificar que Django Está Funcionando

```bash
# En cada servidor, verificar que Django responde
curl http://localhost:8000/inventario/

# Debería mostrar la página principal de Django

# Verificar logs si hay problemas
tail -f django.log
```

### 5.5 Comandos para Controlar Django

```bash
# Ver si Django está corriendo
ps aux | grep runserver

# Detener Django si necesitas
pkill -f runserver

# Reiniciar Django
cd ~/ProvesiWMS
nohup python3 manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &

# Ver logs en tiempo real
tail -f django.log
```

## Paso 6: Probar la Aplicación

```bash
# En CloudShell, obtener URL HTTPS del Load Balancer
terraform output alb_url
```

**Importante sobre HTTPS:**
- La aplicación usa un **certificado autofirmado** generado automáticamente
- Tu navegador mostrará una **advertencia de seguridad** (normal en desarrollo)
- Haz clic en **"Avanzado"** → **"Continuar al sitio"** para acceder
- Una vez dentro, verás la aplicación funcionando con HTTPS completo

**URLs de acceso:**
- **HTTPS (recomendado):** `https://tu-alb-url/inventario/`
- **HTTP:** Redirige automáticamente a HTTPS

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

### Error: Django no responde

```bash
# Verificar que Django está corriendo
ps aux | grep manage.py

# Si no está corriendo, iniciarlo
cd ~/Inventario/ProvesiWMS
python3 manage.py runserver 0.0.0.0:8000

# Verificar variables de entorno si hay errores
echo $DATABASE_HOST
echo $DATABASE_NAME
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

### Método Normal:
```bash
# En CloudShell, ir al directorio terraform
cd Inventario/ProvesiWMS/terraform

# Eliminar toda la infraestructura
terraform destroy
```

Escribe **"yes"** para confirmar.

### Si `terraform destroy` falla (error de provider):

**Opción A: Limpieza manual + reset de Terraform**

1. **En AWS Console, eliminar manualmente en este orden:**
   - EC2 > Load Balancers > Eliminar ALB `provesi-alb-*`
   - EC2 > Target Groups > Eliminar `provesi-app-tg`
   - EC2 > Instances > Terminar todas las instancias `provesi-*`
   - EC2 > Security Groups > Eliminar `provesi-*-sg`
   - IAM > Server certificates > Eliminar `provesi-alb-cert-*`

2. **En CloudShell, limpiar estado de Terraform:**
   ```bash
   cd ~/Inventario/ProvesiWMS/terraform
   
   # Respaldar estado
   cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)
   
   # Limpiar completamente
   rm -rf .terraform/
   rm -f .terraform.lock.hcl
   rm -f terraform.tfstate*
   rm -rf ~/.terraform.d/plugin-cache/
   
   # Verificar que no queden recursos
   echo "Infraestructura limpiada manualmente"
   ```

**Opción B: Reset completo del workspace**

```bash
# En CloudShell, eliminar todo el directorio
cd ~
rm -rf Inventario/

# Volver a clonar para deployment fresco
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario/ProvesiWMS/terraform
terraform init
terraform apply
```

Escribe **"yes"** para confirmar.

## Costos Estimados

- **2x t3.medium**: ~$60/mes
- **1x t3.small (DB)**: ~$30/mes  
- **Load Balancer**: ~$23/mes
- **Total**: ~$113/mes

## Troubleshooting

### Error: "No module named 'django'"

Si obtienes este error, significa que Django no se instaló correctamente en la instancia:

```bash
# Verificar si Django está instalado
python3 -c "import django; print('Django OK')" 2>/dev/null || echo "Django NO instalado"

# Si Django no está instalado, instalarlo manualmente
sudo pip3 install --break-system-packages django==4.2.24 psycopg2-binary djangorestframework djangorestframework-simplejwt django-cors-headers

# Verificar instalación
python3 -c "import django; print('Django version:', django.get_version())"

# Verificar que el repositorio está clonado
ls ~/Inventario/ProvesiWMS/

# Si no existe, clonarlo manualmente
cd ~
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario
git checkout Sprint3V2
```

### Error: "Permission denied: '/tmp/django.log'" o "Unable to configure handler 'file'"

Si obtienes errores de permisos con logs de Django:

```bash
# El problema está en settings.py, se solucionó ya en el repositorio
# Pero si persiste, puedes verificar:

cd ~/Inventario/ProvesiWMS
git pull origin Sprint3V2

# O aplicar el fix manualmente editando wms/settings.py:
# Cambiar LOGGING para usar solo 'console' handler, sin 'file'

# Reintentar ejecutar Django
python3 manage.py runserver 0.0.0.0:8000
```

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

### Error: Load Balancer no funciona (Django funciona pero ALB no)

**Síntoma:** Django responde correctamente en `localhost:8000` en ambos servidores, pero el Load Balancer no funciona.

**Causa más común:** Django no está corriendo en background permanente. Cuando te desconectas de SSH, el proceso se termina.

**Solución:**

```bash
# En AMBOS servidores de aplicación:

# 1. Conectarse al servidor
ssh -i tu-key.pem ubuntu@IP-DEL-SERVIDOR

# 2. Ir al directorio de Django
cd ~/ProvesiWMS

# 3. Verificar si Django está corriendo
ps aux | grep runserver

# 4. Si no está corriendo (o si usaste runserver normal), detener cualquier proceso
pkill -f runserver

# 5. Iniciar Django en BACKGROUND PERMANENTE
nohup python3 manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &

# 6. Verificar que está corriendo
ps aux | grep runserver
curl http://localhost:8000/inventario/

# 7. Verificar logs si hay problemas
tail -f django.log
```

**Verificación del Load Balancer:**

```bash
# Desde CloudShell, obtener URL del ALB
terraform output alb_url

# Probar el Load Balancer (debe mostrar la misma página que localhost:8000)
curl -L http://TU-ALB-URL/inventario/

# Verificar estado de Target Group en AWS Console:
# EC2 > Load Balancers > Tu ALB > Target Groups > Targets
# Ambos servidores deben aparecer como "healthy"
```

**Si los targets aparecen "unhealthy":**

1. Verifica que Django esté corriendo en background en AMBOS servidores
2. Verifica que Django responda en `http://localhost:8000/inventario/` en ambos servidores
3. Verifica que Django esté escuchando en `0.0.0.0:8000` no solo en `127.0.0.1:8000`

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

## 🔧 Proceso Simple Implementado

### ✅ Configuración Automática
- **Terraform** instala Django y todas las dependencias
- **Variables de entorno** preconfiguradas automáticamente
- **Migraciones** aplicadas en el primer servidor
- **Base de datos** lista para usar

### ✅ Inicio Manual Simple
```bash
# En cada servidor
cd ~/Inventario/ProvesiWMS
python3 manage.py runserver 0.0.0.0:8000
```

### ✅ Acceso a la Aplicación
- **Load Balancer URL**: `terraform output alb_url`
- **Puerto externo**: 443 (HTTPS) y 80 (HTTP redirect)
- **Puerto interno**: 8000 (Django development server)

### ✅ Gestión Simple
```bash
# Detener Django
pkill -f runserver

# Iniciar Django en background
cd ~/Inventario/ProvesiWMS
nohup python3 manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &

# Verificar estado
ps aux | grep runserver
```