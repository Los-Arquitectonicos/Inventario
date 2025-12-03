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
