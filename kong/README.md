# Kong API Gateway Configuration

This directory contains the Kong API Gateway configuration for ProvesiWMS.

## 🦍 Kong Overview

Kong acts as the central API Gateway for all microservices:
- **Routes traffic** from ALB to appropriate backend services
- **Provides authentication, rate limiting, and CORS**
- **Enables easy addition of new microservices**
- **Centralizes logging and monitoring**

## 📁 Files

- `kong.yml` - Declarative configuration (services, routes, plugins)
- `README.md` - This file

## 🔧 Current Configuration

### Services Configured:
1. **Django API** - Main inventory management system
   - Routes: `/api/*`, `/inventario/*`, `/admin/*`
   - Target: Django app servers on port 8000

2. **Notifications Service** - Notification microservice
   - Routes: `/notifications/*`, `/api/notifications/*`
   - Target: Notifications service on port 3001

### Plugins Ready:
- JWT Authentication (configured, not yet enabled)
- Rate Limiting (configured for each service)
- CORS (configured for cross-origin requests)
- Request/Correlation ID tracking
- File logging

## 🚀 Usage

### Configuration is automatically deployed via Terraform
The `kong.yml` file is deployed to `/etc/kong/kong.yml` on the Kong instance.

### Manual Configuration Update
1. SSH to Kong instance: `ssh ubuntu@<kong-ip>`
2. Edit configuration: `sudo nano /etc/kong/kong.yml`
3. Reload Kong: `sudo kong reload`

### Adding New Services
Add to the `services` section in `kong.yml`:

```yaml
services:
  - name: new-service-name
    url: http://backend-ip:port
    retries: 3
    connect_timeout: 5000
    routes:
      - name: new-service-routes
        paths:
          - /new-service
        strip_path: false
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 100
```

## 🧪 Testing Configuration

```bash
# Test service routing via Kong
curl http://<kong-ip>:8000/api/        # → Django
curl http://<kong-ip>:8000/notifications/  # → Notifications

# Via ALB (production)
curl https://<alb-domain>/api/
curl https://<alb-domain>/notifications/
```

## 🔑 Environment Variables

The configuration uses these variables (replaced by Terraform):
- `${DJANGO_PRIVATE_IP_1}` - IP of first Django server
- `${NOTIFICATIONS_PRIVATE_IP}` - IP of notifications service
- `${DJANGO_SECRET_KEY}` - JWT secret key

## 📊 Monitoring

Kong logs all requests to:
- `/var/log/kong/access.log` - Request logs
- `/var/log/kong/error.log` - Error logs

Admin API available at `http://localhost:8001` (SSH tunnel required).

## 🔒 Security Notes

- Admin API only accessible via localhost
- JWT authentication ready but disabled initially
- Rate limiting configured per service
- All backend services only accept Kong traffic

## 🎯 Future Enhancements

1. **Enable JWT Authentication**
2. **Add Analytics Service routes**
3. **Configure SSL termination in Kong**
4. **Add custom plugins for business logic**
5. **Integrate with monitoring services**