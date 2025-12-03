# Kong API Gateway - ProvesiWMS

## 🏗️ Arquitectura

```
                    ┌──────────────────────────────────────┐
                    │              INTERNET                │
                    └─────────────────┬────────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────────┐
                    │         KONG API GATEWAY             │
                    │      ⭐ ÚNICO PUNTO DE ENTRADA ⭐     │
                    │                                      │
                    │   HTTPS :443  │  HTTP :8000          │
                    │   Status :8100                       │
                    └─────────────────┬────────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────────┐
                    │           ALB (interno)              │
                    │    ⚠️  Solo accesible desde Kong     │
                    │              HTTPS :443              │
                    └─────────────────┬────────────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
           ┌─────────────────┐               ┌─────────────────┐
           │  Django App 1   │               │  Django App 2   │
           │  (Gunicorn)     │               │  (Gunicorn)     │
           │     :8000       │               │     :8000       │
           └─────────────────┘               └─────────────────┘
                     │                                 │
                     └────────────────┬────────────────┘
                                      ▼
                          ┌─────────────────┐
                          │   PostgreSQL    │
                          │     :5432       │
                          └─────────────────┘
```

### Acceso a la aplicación:

| URL | Descripción |
|-----|-------------|
| `https://<kong-ip>/inventario/` | ⭐ Aplicación principal |
| `https://<kong-ip>/api/` | ⭐ API REST |
| `https://<kong-ip>/admin/` | Panel de administración |
| `http://<kong-ip>:8000/...` | Mismo que arriba (HTTP) |
| `http://<kong-ip>:8100/status` | Health check de Kong |

> ⚠️ **Nota**: El ALB ya NO es accesible directamente. Todo el tráfico debe pasar por Kong.

---

## 🚀 Post-Despliegue

**No se requiere configuración adicional.** Todo está automatizado.

### Obtener URL de acceso

```bash
cd ~/Inventario/terraform

# Ver resumen de acceso
terraform output access_summary

# O individualmente
terraform output kong_public_ip
terraform output kong_https_url
```

### Verificar que funciona

```bash
KONG_IP=$(terraform output -raw kong_public_ip)

# Health check
curl http://$KONG_IP:8100/status

# Aplicación
curl -k https://$KONG_IP/inventario/
```

---

## 🔧 Troubleshooting

### Verificar desde la instancia Kong

```bash
# Conectarse via EC2 Instance Connect

# Estado de Kong
sudo kong health
sudo systemctl status kong

# Ver log de instalación
cat /var/log/kong-install.log

# Ver configuración actual
cat /etc/kong/kong.yml
```

### Kong no responde

```bash
# Reiniciar Kong
sudo systemctl restart kong

# Ver errores
sudo journalctl -u kong -n 50
sudo tail -50 /var/log/kong/error.log
```

### Error 502/504 desde Kong

El ALB o Django no están disponibles:

```bash
# Verificar que el ALB responde (desde instancia Kong)
curl -k https://<alb-internal-dns>/health

# Ver logs de Kong
sudo tail -f /var/log/kong/error.log
```

---

## 📋 Comandos Útiles

```bash
# === KONG ===
sudo kong health              # Estado de Kong
sudo kong reload              # Recargar configuración
sudo systemctl status kong    # Estado del servicio
sudo tail -f /var/log/kong/access.log  # Logs de acceso
sudo tail -f /var/log/kong/error.log   # Logs de errores

# === DJANGO (en servidores app) ===
sudo systemctl status django  # Estado de Django
sudo systemctl restart django # Reiniciar Django
sudo journalctl -u django -f  # Logs de Django
```

---

## 🔌 Agregar Microservicios

Editar `/etc/kong/kong.yml` en el servidor Kong:

```yaml
services:
  # ... servicios existentes ...
  
  - name: nuevo-servicio
    url: http://<ip-privada>:<puerto>
    routes:
      - name: nuevo-servicio-route
        paths:
          - /nuevo-path
```

Luego: `sudo kong reload`

---

## 🔐 Seguridad

- **Kong**: Único punto de entrada público (443, 8000, 8100, 22)
- **ALB**: Solo accesible desde Kong (Security Group restringido)
- **Django**: Solo accesible desde ALB (Security Group restringido)
- **PostgreSQL**: Solo accesible desde Django (Security Group restringido)

---

## 📁 Archivos de Configuración

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| `kong.conf` | `/etc/kong/kong.conf` | Configuración del servidor |
| `kong.yml` | `/etc/kong/kong.yml` | Servicios y rutas |
| Install log | `/var/log/kong-install.log` | Log de instalación |
| Access log | `/var/log/kong/access.log` | Requests |
| Error log | `/var/log/kong/error.log` | Errores |

