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

```bash
# Ir al directorio de la aplicación
cd /opt/apps/Inventario/ProvesiWMS

# Configurar usuarios iniciales (solo en el primer servidor)
python3 setup_users.py

# Iniciar servidor Django
sudo python3 manage.py runserver 0.0.0.0:8080
```

### 5.4 Configurar el Servidor 2

```bash
# Ir al directorio
cd /opt/apps/Inventario/ProvesiWMS

# Iniciar servidor Django
sudo python3 manage.py runserver 0.0.0.0:8080
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

### Reiniciar Servidor Django

```bash
# Detener servidor actual
sudo pkill -f "manage.py runserver"

# Iniciar nuevamente
sudo python3 manage.py runserver 0.0.0.0:8080
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

**¡Listo!** Tu aplicación ProvesiWMS está corriendo en AWS con autenticación JWT completa.