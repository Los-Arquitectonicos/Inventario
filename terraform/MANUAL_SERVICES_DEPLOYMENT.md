# Deployment Manual de Kong Gateway y Notifications Service

Esta guía te ayudará a iniciar manualmente los servicios de Kong API Gateway y Notifications en sus respectivas instancias EC2.

## Tabla de Contenidos
- [1. Kong API Gateway](#1-kong-api-gateway)
- [2. Notifications Service](#2-notifications-service)
- [3. Verificación de Servicios](#3-verificación-de-servicios)
- [4. Troubleshooting](#4-troubleshooting)
- [5. Comandos de Gestión](#5-comandos-de-gestión)

---

## 1. Kong API Gateway

### 1.1 Conectarse a la Instancia de Kong

Desde **CloudShell**, obtén la IP de Kong:

```bash
cd ~/Inventario/terraform
terraform output kong_gateway_public_ip
```

Conecta por SSH:

```bash
ssh ubuntu@<KONG_PUBLIC_IP>
```

### 1.2 Verificar Estado de Kong

```bash
# Verificar si Kong está instalado
kong version

# Verificar si Kong está corriendo
ps aux | grep kong | grep -v grep

# Verificar procesos nginx (Kong usa nginx internamente)
ps aux | grep nginx | grep -v grep

# Verificar puertos en escucha
sudo netstat -tulpn | grep -E ':(8000|8001|8443|8444)'
```

### 1.3 Iniciar Kong (Si no está corriendo)

```bash
# Verificar que existe el archivo de configuración
ls -la /etc/kong/kong.conf
cat /etc/kong/kong.yml

# Iniciar Kong con la configuración
sudo kong start -c /etc/kong/kong.conf

# Verificar que inició correctamente
sudo kong health

# Ver logs si hay problemas
sudo tail -f /var/log/kong/error.log
```

### 1.4 Verificar Configuración de Kong

```bash
# Ver configuración actual
curl http://localhost:8001/

# Listar servicios configurados
curl http://localhost:8001/services

# Listar rutas configuradas
curl http://localhost:8001/routes

# Probar que Kong responde
curl http://localhost:8000/
```

### 1.5 Reconfigurar Kong (Si es necesario)

Si necesitas actualizar la configuración de rutas:

```bash
# Obtener IPs privadas de los backends
DJANGO_IP=$(terraform output -raw app_server_1_private_ip)
NOTIFICATIONS_IP=$(terraform output -raw notifications_private_ip)

# Editar configuración de Kong
sudo nano /etc/kong/kong.yml
```

Configuración esperada en `kong.yml`:

```yaml
_format_version: "3.0"
services:
  - name: django-api
    url: http://<DJANGO_PRIVATE_IP>:8000
    routes:
      - name: django-routes
        paths: ["/api", "/inventario", "/admin"]
  - name: notifications
    url: http://<NOTIFICATIONS_PRIVATE_IP>:3001
    routes:
      - name: notification-routes
        paths: ["/notifications"]
```

Después de editar:

```bash
# Recargar configuración
sudo kong reload -c /etc/kong/kong.conf

# Verificar que no hay errores
sudo kong health
```

---

## 2. Notifications Service

### 2.1 Conectarse a la Instancia de Notifications

Desde **CloudShell**, obtén la IP de Notifications:

```bash
cd ~/Inventario/terraform
terraform output notifications_public_ip
```

Conecta por SSH:

```bash
ssh ubuntu@<NOTIFICATIONS_PUBLIC_IP>
```

### 2.2 Verificar Estado del Servicio

```bash
# Verificar si Node.js está instalado
node --version
npm --version

# Verificar si PM2 está instalado
pm2 --version

# Ver procesos PM2
pm2 list

# Ver estado detallado del servicio
pm2 show notifications

# Verificar puertos en escucha
sudo netstat -tulpn | grep 3001
```

### 2.3 Iniciar Notifications Service (Si no está corriendo)

```bash
# Ir al directorio del proyecto
cd /home/ubuntu/Inventario/notifications

# Verificar que existe el archivo .env
cat .env

# Instalar dependencias si es necesario
npm install

# Iniciar con PM2
pm2 start server.js --name notifications

# Guardar configuración de PM2
pm2 save

# Verificar que inició correctamente
pm2 list
pm2 logs notifications --lines 50
```

### 2.4 Verificar Configuración del Servicio

```bash
# Ver archivo .env
cat /home/ubuntu/Inventario/notifications/.env

# Probar endpoints localmente
curl http://localhost:3001/health
curl http://localhost:3001/
curl http://localhost:3001/test
```

Configuración esperada en `.env`:

```bash
PORT=3001
HOST=0.0.0.0
MONGO_URI=mongodb://<MONGODB_PRIVATE_IP>:27017/provesi_notifications
JWT_SECRET=<DJANGO_SECRET_KEY>
```

### 2.5 Reconfigurar Notifications (Si es necesario)

```bash
# Editar archivo .env
nano /home/ubuntu/Inventario/notifications/.env

# Después de editar, reiniciar el servicio
pm2 restart notifications

# Ver logs en tiempo real
pm2 logs notifications
```

---

## 3. Verificación de Servicios

### 3.1 Desde la Instancia de Kong

```bash
# Probar acceso a Django desde Kong
curl http://<DJANGO_PRIVATE_IP>:8000/inventario/

# Probar acceso a Notifications desde Kong
curl http://<NOTIFICATIONS_PRIVATE_IP>:3001/health

# Probar routing de Kong
curl http://localhost:8000/inventario/
curl http://localhost:8000/notifications/health
```

### 3.2 Desde tu Máquina Local

```bash
# Obtener URL del ALB
ALB_URL=$(cd ~/Inventario/terraform && terraform output -raw alb_dns_name)

# Probar routing a través de ALB → Kong → Django
curl -k https://${ALB_URL}/inventario/

# Probar routing a través de ALB → Kong → Notifications
curl -k https://${ALB_URL}/notifications/health
curl -k https://${ALB_URL}/notifications/test
```

### 3.3 Verificar Target Groups en AWS Console

1. Ve a **EC2 > Load Balancers**
2. Selecciona tu ALB (`provesi-alb-*`)
3. Ve a la pestaña **Target groups**
4. Verifica que Kong aparezca como **healthy**

---

## 4. Troubleshooting

### 4.1 Kong no responde

**Síntoma:** ALB da 502 Bad Gateway

**Diagnóstico:**

```bash
# Conectar a Kong
ssh ubuntu@<KONG_IP>

# Ver logs de error
sudo tail -f /var/log/kong/error.log
sudo tail -f /var/log/kong/access.log

# Ver logs de user-data (script de inicio)
sudo cat /var/log/user-data.log

# Ver estado de nginx (Kong usa nginx)
ps aux | grep nginx
```

**Soluciones:**

```bash
# Opción 1: Reiniciar Kong
sudo kong restart -c /etc/kong/kong.conf

# Opción 2: Detener y volver a iniciar
sudo kong stop
sudo kong start -c /etc/kong/kong.conf

# Opción 3: Reinstalar Kong si hay problemas
sudo apt-get remove --purge kong -y
wget -O kong.deb "https://download.konghq.com/gateway-3.x-ubuntu-noble/pool/all/k/kong/kong_3.9.0.0_amd64.deb"
sudo dpkg -i kong.deb
sudo apt-get install -f -y

# Recrear configuración
sudo mkdir -p /etc/kong
sudo nano /etc/kong/kong.conf
sudo nano /etc/kong/kong.yml

# Iniciar
sudo kong start -c /etc/kong/kong.conf
```

### 4.2 Notifications no responde

**Síntoma:** Kong no puede conectar con Notifications

**Diagnóstico:**

```bash
# Conectar a Notifications
ssh ubuntu@<NOTIFICATIONS_IP>

# Ver estado de PM2
pm2 list
pm2 logs notifications --lines 100

# Ver logs del sistema
sudo journalctl -u pm2-ubuntu -n 50 --no-pager

# Verificar conectividad con MongoDB
curl http://<MONGODB_PRIVATE_IP>:27017/
```

**Soluciones:**

```bash
# Opción 1: Reiniciar servicio
pm2 restart notifications

# Opción 2: Detener y volver a iniciar
pm2 stop notifications
pm2 delete notifications
cd /home/ubuntu/Inventario/notifications
pm2 start server.js --name notifications
pm2 save

# Opción 3: Reinstalar dependencias
cd /home/ubuntu/Inventario/notifications
rm -rf node_modules
npm install
pm2 restart notifications

# Opción 4: Verificar archivo .env
cat .env
# Si falta o está mal, recrearlo con la configuración correcta
```

### 4.3 Kong puede acceder pero ALB no

**Síntoma:** `curl http://localhost:8000` funciona en Kong, pero ALB da timeout

**Causa:** Problema de grupos de seguridad

**Solución:**

1. Ve a **EC2 > Security Groups**
2. Busca el grupo `provesi-kong-sg`
3. Verifica que tenga regla de entrada:
   - **Tipo:** Custom TCP
   - **Puerto:** 8000
   - **Origen:** Security Group del ALB (`provesi-alb-sg`)

4. Busca el grupo `provesi-alb-sg`
5. Verifica que tenga regla de salida:
   - **Tipo:** All traffic
   - **Destino:** 0.0.0.0/0

### 4.4 Rutas de Kong no funcionan

**Síntoma:** Kong responde pero rutas dan 404

**Diagnóstico:**

```bash
# Ver rutas configuradas
curl http://localhost:8001/routes

# Ver servicios configurados
curl http://localhost:8001/services
```

**Solución:**

```bash
# Verificar archivo de configuración
sudo cat /etc/kong/kong.yml

# Si está mal o vacío, recrearlo
sudo nano /etc/kong/kong.yml

# Recargar configuración
sudo kong reload -c /etc/kong/kong.conf

# Verificar que cargó correctamente
curl http://localhost:8001/routes
```

---

## 5. Comandos de Gestión

### 5.1 Kong

```bash
# Iniciar Kong
sudo kong start -c /etc/kong/kong.conf

# Detener Kong
sudo kong stop

# Reiniciar Kong
sudo kong restart -c /etc/kong/kong.conf

# Recargar configuración sin downtime
sudo kong reload -c /etc/kong/kong.conf

# Verificar salud de Kong
sudo kong health

# Ver configuración activa
curl http://localhost:8001/

# Ver logs en tiempo real
sudo tail -f /var/log/kong/error.log
sudo tail -f /var/log/kong/access.log
```

### 5.2 Notifications

```bash
# Ver todos los procesos PM2
pm2 list

# Ver logs en tiempo real
pm2 logs notifications

# Ver logs históricos
pm2 logs notifications --lines 200

# Reiniciar servicio
pm2 restart notifications

# Detener servicio
pm2 stop notifications

# Eliminar servicio de PM2
pm2 delete notifications

# Iniciar nuevamente
cd /home/ubuntu/Inventario/notifications
pm2 start server.js --name notifications

# Guardar configuración
pm2 save

# Ver uso de recursos
pm2 monit

# Ver información detallada
pm2 show notifications
```

### 5.3 Script de Verificación Completa

Ejecuta este comando desde **CloudShell** para verificar todos los servicios:

```bash
cd ~/Inventario/terraform
./diagnose_infrastructure.sh
```

---

## 6. Inicio Automático después de Reboot

### 6.1 Kong

Kong ya está configurado para iniciar automáticamente si se instaló correctamente. Para verificar:

```bash
# Ver si Kong tiene un servicio systemd
sudo systemctl status kong

# Si no existe, Kong se iniciará con el archivo de configuración
# en el próximo boot usando el script de user-data
```

### 6.2 Notifications

PM2 ya está configurado para inicio automático:

```bash
# Verificar configuración de startup
pm2 startup

# Verificar que la configuración está guardada
pm2 save

# Ver qué procesos se iniciarán
pm2 list
```

---

## 7. Resumen de Puertos

| Servicio | Puerto | Protocolo | Acceso |
|----------|--------|-----------|--------|
| Kong Proxy | 8000 | HTTP | Público (desde ALB) |
| Kong Admin | 8001 | HTTP | Local (127.0.0.1) |
| Notifications | 3001 | HTTP | Privado (desde Kong) |
| Django | 8000 | HTTP | Privado (desde Kong) |
| MongoDB | 27017 | TCP | Privado (desde Notifications) |

---

## 8. URLs de Acceso Final

Después de iniciar todos los servicios:

```bash
# Obtener URL del ALB
cd ~/Inventario/terraform
terraform output alb_url

# Las rutas disponibles son:
# - https://<ALB_URL>/notifications/health
# - https://<ALB_URL>/notifications/test
# - https://<ALB_URL>/inventario/
# - https://<ALB_URL>/api/
# - https://<ALB_URL>/admin/
```

---

## 9. Checklist de Deployment

- [ ] Kong instalado y corriendo
- [ ] Kong responde en puerto 8000
- [ ] Kong tiene configuración correcta en `/etc/kong/kong.yml`
- [ ] Notifications corriendo con PM2
- [ ] Notifications responde en puerto 3001
- [ ] MongoDB accesible desde Notifications
- [ ] Target Group del ALB muestra Kong como "healthy"
- [ ] Rutas de Kong funcionan correctamente
- [ ] ALB → Kong → Django funciona
- [ ] ALB → Kong → Notifications funciona

---

**¡Listo!** Con esta guía puedes iniciar y gestionar manualmente los servicios de Kong y Notifications en AWS.
