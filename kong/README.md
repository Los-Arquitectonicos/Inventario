# Kong API Gateway - ProvesiWMS Service Discovery

Este directorio contiene la configuración de Kong API Gateway para el sistema ProvesiWMS.

## Arquitectura

```
Internet → ALB (HTTPS:443) → Kong Gateway (EC2:8000) → Servicios Backend
                                    │
                                    ├→ Django API (:8000) - /api, /inventario, /admin
                                    ├→ Notifications (:3001) - /notifications
                                    └→ Config Service (:3003) - /config, /features
```

---

## 🚀 Guía Rápida: Acceder a la Aplicación vía Kong

### Paso 1: Obtener las IPs después del despliegue

Después de ejecutar `terraform apply`, obtén las IPs necesarias:

```bash
cd ~/Inventario/terraform

# Ver todos los outputs
terraform output

# O específicamente:
terraform output kong_gateway_public_ip
terraform output alb_dns_name
terraform output app_server_1_private_ip
terraform output app_server_2_private_ip
```

### Paso 2: Verificar que Kong está funcionando

```bash
# Conectar por SSH a Kong
ssh ubuntu@$(terraform output -raw kong_gateway_public_ip)

# Verificar estado de Kong
sudo kong health

# Ver logs de instalación (si hay problemas)
sudo cat /var/log/kong-install.log
```

### Paso 3: Verificar que los servidores Django están configurados en Kong

```bash
# En el servidor Kong, verificar la configuración
cat /etc/kong/kong.yml | grep -A5 "targets:"

# Verificar que Kong puede alcanzar Django
curl -s http://localhost:8000/inventario/
```

### Paso 4: Acceder a la aplicación

Una vez todo está funcionando, accede a través del ALB:

```bash
# Obtener URL del ALB
ALB_DNS=$(terraform output -raw alb_dns_name)

# Acceder a la API (a través de Kong)
curl -k "https://$ALB_DNS/inventario/"
curl -k "https://$ALB_DNS/api/"
curl -k "https://$ALB_DNS/admin/"

# Health check de Kong
curl -k "https://$ALB_DNS/kong-health"
```

> **Nota:** Usa `-k` porque el certificado SSL es autofirmado.

### Paso 5: Probar desde el navegador

Abre en tu navegador:
- `https://<alb-dns-name>/inventario/` - Aplicación principal
- `https://<alb-dns-name>/api/` - API REST
- `https://<alb-dns-name>/admin/` - Panel de administración Django

---

## 🔧 Troubleshooting Post-Despliegue

### Kong no responde (502 Bad Gateway)

1. **Verificar que Kong está corriendo:**
   ```bash
   ssh ubuntu@<kong-ip>
   sudo kong health
   sudo systemctl status kong
   ```

2. **Verificar que Django está corriendo:**
   ```bash
   # Desde Kong, probar conectividad a Django
   curl http://<django-private-ip>:8000/inventario/
   ```

3. **Ver logs de Kong:**
   ```bash
   sudo tail -f /var/log/kong/error.log
   ```

### Los servidores Django no están en el upstream

Si los targets de Django no se configuraron correctamente durante el despliegue:

```bash
# SSH a Kong
ssh ubuntu@<kong-ip>

# Editar la configuración
sudo nano /etc/kong/kong.yml

# Buscar la sección 'targets' y verificar/corregir las IPs:
#     targets:
#       - target: <django-private-ip-1>:8000
#         weight: 100
#       - target: <django-private-ip-2>:8000
#         weight: 100

# Recargar Kong
sudo kong reload
```

### Verificar que el ALB está enrutando a Kong

```bash
# Ver el target group de Kong en AWS Console
# O verificar desde la terminal:
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names provesi-kong-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)
```

### Django no está iniciado

```bash
# SSH a uno de los servidores Django
ssh ubuntu@<django-public-ip>

# Iniciar Django manualmente
cd ~/Inventario/ProvesiWMS
source /opt/apps/Inventario/venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# O con gunicorn para producción:
gunicorn --bind 0.0.0.0:8000 wms.wsgi:application
```

---

## Archivos de Configuración

| Archivo | Descripción |
|---------|-------------|
| `kong.yml` | Configuración declarativa de servicios, rutas y plugins |
| `kong.conf` | Configuración del servidor Kong (puertos, logging, etc.) |

## Modo de Operación

Kong opera en **modo DB-less** (sin base de datos), usando configuración declarativa YAML.

**Ventajas:**
- Sin dependencia de PostgreSQL/Cassandra adicional
- Configuración versionable en Git
- Despliegue más simple y reproducible
- Menor consumo de recursos

## Servicios Configurados

### 1. Django API (Principal)
- **URL interno:** `http://DJANGO_UPSTREAM:8000`
- **Rutas:** `/api/*`, `/inventario/*`, `/admin/*`
- **Plugins:** Rate limiting (200/min), CORS

### 2. Notifications
- **URL interno:** `http://NOTIFICATIONS_UPSTREAM:3001`
- **Rutas:** `/notifications/*`
- **Plugins:** Rate limiting (100/min), CORS

### 3. Config Service
- **URL interno:** `http://CONFIG_UPSTREAM:3003`
- **Rutas:** `/config/*`, `/features/*`
- **Plugins:** Rate limiting (50/min)

## Puertos

| Puerto | Uso |
|--------|-----|
| 8000 | Proxy HTTP (recibe tráfico del ALB) |
| 8001 | Admin API (solo localhost) |
| 8100 | Status/Health checks |

## Health Check

Kong expone un endpoint de health check en:
```
http://localhost:8100/status
```

El ALB usa este endpoint para verificar la salud de Kong.

## Comandos Útiles

### Ver estado de Kong
```bash
sudo kong health
```

### Recargar configuración (sin downtime)
```bash
sudo kong reload
```

### Ver logs
```bash
# Logs de acceso
sudo tail -f /var/log/kong/access.log

# Logs de error
sudo tail -f /var/log/kong/error.log
```

### Acceder a Admin API (vía SSH tunnel)
```bash
# Desde tu máquina local
ssh -L 8001:localhost:8001 ubuntu@<kong-public-ip>

# En otra terminal
curl http://localhost:8001/services
curl http://localhost:8001/routes
curl http://localhost:8001/plugins
curl http://localhost:8001/status
```

### Verificar servicios registrados
```bash
curl http://localhost:8001/services | jq
```

### Verificar rutas
```bash
curl http://localhost:8001/routes | jq
```

## Agregar Nuevo Servicio

1. Editar `/etc/kong/kong.yml` en el servidor Kong
2. Agregar nuevo servicio y ruta:

```yaml
services:
  - name: nuevo-servicio
    url: http://IP_PRIVADA:PUERTO
    routes:
      - name: nuevo-servicio-route
        paths:
          - /nuevo-path
        strip_path: false
    plugins:
      - name: rate-limiting
        config:
          minute: 100
```

3. Recargar Kong:
```bash
sudo kong reload
```

## Configurar Upstreams Dinámicos

Después del despliegue, agregar los targets reales:

```bash
# Agregar servidor Django 1
curl -X POST http://localhost:8001/upstreams/DJANGO_UPSTREAM/targets \
  -d "target=<django-private-ip-1>:8000"

# Agregar servidor Django 2
curl -X POST http://localhost:8001/upstreams/DJANGO_UPSTREAM/targets \
  -d "target=<django-private-ip-2>:8000"
```

## Troubleshooting

### Kong no inicia
```bash
# Verificar configuración
sudo kong check /etc/kong/kong.conf

# Ver logs de error
sudo journalctl -u kong -f
```

### Servicio no responde
```bash
# Verificar que el servicio está registrado
curl http://localhost:8001/services/django-api

# Verificar rutas
curl http://localhost:8001/services/django-api/routes

# Probar conectividad directa
curl http://<backend-ip>:8000/inventario/
```

### Rate limiting muy restrictivo
Modificar en `kong.yml`:
```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 500  # Aumentar límite
```

## Seguridad

- **Admin API:** Solo accesible vía localhost (requiere SSH tunnel)
- **Proxy:** Solo acepta tráfico desde el ALB (Security Group)
- **Headers:** Headers de versión deshabilitados
- **Logs:** Todos los requests son logueados

## Monitoreo

### Métricas disponibles en `/status`
- Memoria utilizada
- Conexiones activas
- Requests procesados
- Estado de plugins

### Integración con CloudWatch
Los logs de Kong se pueden enviar a CloudWatch usando el plugin `http-log` o CloudWatch Agent.

## Actualizaciones

Para actualizar la configuración:

1. Modificar `kong/kong.yml` localmente
2. Copiar al servidor:
   ```bash
   scp kong/kong.yml ubuntu@<kong-ip>:/tmp/
   sudo mv /tmp/kong.yml /etc/kong/kong.yml
   ```
3. Recargar:
   ```bash
   sudo kong reload
   ```

---

## 📋 Resumen de Comandos Post-Despliegue

```bash
# === DESDE TU MÁQUINA LOCAL ===

# 1. Ir al directorio terraform
cd ~/Inventario/terraform

# 2. Obtener información del despliegue
terraform output

# 3. Guardar variables útiles
export ALB_DNS=$(terraform output -raw alb_dns_name)
export KONG_IP=$(terraform output -raw kong_gateway_public_ip)

# 4. Probar acceso a la aplicación
curl -k "https://$ALB_DNS/inventario/"

# === DESDE EL SERVIDOR KONG (vía SSH) ===

# Conectar a Kong
ssh ubuntu@$KONG_IP

# Verificar estado
sudo kong health

# Ver configuración actual
cat /etc/kong/kong.yml

# Ver logs en tiempo real
sudo tail -f /var/log/kong/access.log

# Recargar configuración después de cambios
sudo kong reload
```

## 🔗 URLs de la Aplicación

| Endpoint | URL | Descripción |
|----------|-----|-------------|
| Inventario | `https://<alb-dns>/inventario/` | Página principal |
| API REST | `https://<alb-dns>/api/` | Endpoints de la API |
| Admin Django | `https://<alb-dns>/admin/` | Panel de administración |
| Kong Health | `https://<alb-dns>/kong-health` | Health check de Kong |

