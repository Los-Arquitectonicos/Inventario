# Kong API Gateway - Deployment Guide

## 🦍 Overview

Kong has been implemented as a centralized API Gateway for ProvesiWMS, providing:

- **Centralized routing** for all microservices
- **Future-ready architecture** for easy service addition
- **Security layer** for authentication and rate limiting
- **Single point of entry** via ALB

## 🏗️ Architecture

```
Internet → ALB (HTTPS/443) → Kong Gateway (EC2) → Backend Services
                                         ├→ Django App (port 8000)
                                         ├→ Notifications (port 3001)
                                         └→ Future Services...
```

## 🚀 Quick Deployment

### 1. Deploy Kong Gateway
```bash
cd /path/to/Inventario/terraform
./deploy_kong_gateway.sh
```

### 2. Test the deployment
```bash
./test_kong_gateway.sh
```

## 📡 Service Routing

Kong routes requests based on path patterns:

| Path | Target Service | Description |
|------|---------------|-------------|
| `/api/*` | Django Backend | Main API endpoints |
| `/inventario/*` | Django Backend | Inventory management |
| `/admin/*` | Django Backend | Django admin interface |
| `/notifications/*` | Notifications Service | Notification endpoints |

## 🔧 Kong Configuration

### Current Configuration (`kong.yml`)
- **Database**: DB-less mode (declarative config)
- **Services**: Django API, Notifications
- **Routes**: Path-based routing
- **Plugins**: Ready for JWT, rate limiting, CORS

### Kong Instance Details
- **Instance Type**: t3.small (2 vCPU, 2GB RAM)
- **Ports**: 8000 (proxy), 8001 (admin - localhost only)
- **Health Check**: `/` endpoint
- **Logs**: `/var/log/kong/`

## 🧪 Testing Kong

### Via ALB (Recommended)
```bash
# Get ALB URL from terraform output
ALB_URL=$(terraform output -raw api_gateway_url)

# Test Django routes
curl $ALB_URL/api/
curl $ALB_URL/inventario/

# Test notifications
curl $ALB_URL/notifications/health
```

### Direct Kong Access
```bash
# Get Kong IP
KONG_IP=$(terraform output -raw kong_gateway_public_ip)

# Test directly
curl http://$KONG_IP:8000/api/
curl http://$KONG_IP:8000/notifications/
```

## 🔑 Kong Administration

### Access Kong Admin API
```bash
# SSH tunnel to Kong instance
ssh -L 8001:localhost:8001 ubuntu@<kong-public-ip>

# In another terminal, use Admin API
curl http://localhost:8001/services
curl http://localhost:8001/routes
curl http://localhost:8001/status
```

### Common Kong Admin Commands
```bash
# List all services
curl http://localhost:8001/services

# List all routes
curl http://localhost:8001/routes

# Kong health
curl http://localhost:8001/status

# List plugins
curl http://localhost:8001/plugins
```

## 📝 Configuration Updates

### Update Kong Configuration
1. SSH to Kong instance
2. Edit `/etc/kong/kong.yml`
3. Reload configuration: `sudo kong reload`

### Add New Microservice
Update `/etc/kong/kong.yml`:
```yaml
services:
  # Existing services...
  
  - name: new-service
    url: http://backend-ip:port
    routes:
      - name: new-service-routes
        paths:
          - /new-service
```

## 🎯 Next Steps

### Phase 2: Security Implementation
1. **JWT Authentication**:
   ```yaml
   plugins:
     - name: jwt
       config:
         claims_to_verify: ["exp"]
         header_names: ["Authorization"]
   ```

2. **Rate Limiting**:
   ```yaml
   plugins:
     - name: rate-limiting
       config:
         minute: 100
         policy: local
   ```

3. **CORS Configuration**:
   ```yaml
   plugins:
     - name: cors
       config:
         origins: ["https://your-domain.com"]
         credentials: true
   ```

### Phase 3: Additional Services
- Analytics Service (Lambda integration)
- Order Workflow Service
- Configuration Service
- User Management Service

## 🔍 Monitoring & Troubleshooting

### Check Kong Status
```bash
# On Kong instance
sudo systemctl status kong
sudo kong health

# Check logs
sudo tail -f /var/log/kong/error.log
sudo tail -f /var/log/kong/access.log
```

### Common Issues

#### Kong not starting
- Check configuration: `sudo kong check /etc/kong/kong.conf`
- Validate YAML: `yamllint /etc/kong/kong.yml`
- Check logs: `sudo journalctl -u kong -f`

#### Routing not working
- Verify routes: `curl localhost:8001/routes`
- Check service health: `curl localhost:8001/services/{service-name}/health`
- Test backend directly: `curl http://backend-ip:port`

#### ALB health check failing
- Verify target group health check path
- Ensure Kong is responding on port 8000
- Check security group rules

## 📊 Performance & Scaling

### Current Capacity
- **Instance**: t3.small can handle 100-500 req/s
- **Latency**: ~1-5ms additional latency from Kong
- **Throughput**: Limited by backend services, not Kong

### Scaling Options
1. **Vertical Scaling**: Upgrade to t3.medium/large
2. **Horizontal Scaling**: Add second Kong instance
3. **Load Balancing**: Multiple Kong instances behind ALB

## 🛡️ Security Considerations

- Kong Admin API only accessible via localhost (SSH tunnel required)
- All backend services only accept traffic from Kong security group
- JWT validation centralizes authentication
- Rate limiting prevents abuse

## 💰 Cost Impact
- Additional ~$15-20/month for Kong instance
- Minimal data transfer costs
- Significant operational benefits

## 🔄 Rollback Plan

If issues occur, rollback by:
1. Update ALB listener to route directly to Django target group
2. Comment out Kong resources in terraform
3. Apply changes: `terraform apply`
4. Services remain accessible during rollback