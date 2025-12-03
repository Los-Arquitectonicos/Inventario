# Notifications Service - Standalone Deployment

This document describes the updated deployment for the notifications service as a standalone microservice.

## 🎯 Overview

The notifications service has been reconfigured to run independently:

- **No longer integrated with ALB** - Runs standalone on port 3001
- **Direct public access** - Accessible via `http://<public-ip>:3001`
- **Simplified deployment** - Automatic setup via Terraform
- **Independent operation** - No dependency on Django application

## 🚀 Quick Deployment

### 1. Navigate to terraform directory
```bash
cd /path/to/Inventario/ProvesiWMS/terraform
```

### 2. Run the deployment script
```bash
./deploy_notifications.sh
```

This script will:
- Initialize Terraform if needed
- Validate configuration
- Show deployment plan
- Deploy infrastructure
- Display connection information

### 3. Test the service
```bash
./test_notifications.sh
```

## 📋 Manual Deployment Steps

If you prefer manual control:

### 1. Initialize Terraform
```bash
terraform init
```

### 2. Plan deployment
```bash
terraform plan
```

### 3. Apply changes
```bash
terraform apply
```

### 4. Get outputs
```bash
terraform output
```

## 🔧 What Changed

### Infrastructure Changes:
1. **Security Group**: Now allows public access on port 3001 (instead of only ALB)
2. **Instance Configuration**: Simplified deployment process
3. **ALB Integration**: Removed target groups and listener rules
4. **Branch**: Now deploys from `notificaciones` branch

### Benefits:
- ✅ Direct testing without ALB complexity
- ✅ Faster deployment and iteration
- ✅ Clear separation from main application
- ✅ Independent scaling and management

## 🧪 Testing the Service

After deployment, you can test:

### Health Check
```bash
curl http://<public-ip>:3001/health
```

### Register Admin User
```bash
curl -X POST http://<public-ip>:3001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@provesi.com",
    "password": "admin123",
    "role": "admin"
  }'
```

### Login
```bash
curl -X POST http://<public-ip>:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@provesi.com", 
    "password": "admin123"
  }'
```

### Create Notification
```bash
curl -X POST http://<public-ip>:3001/api/notifications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Test Notification",
    "message": "Test message",
    "type": "info",
    "recipients": ["test@example.com"]
  }'
```

## 📊 Service Information

### Endpoints:
- **Health**: `/health`
- **Auth**: `/api/auth/*`
- **Notifications**: `/api/notifications/*`

### Default Credentials:
- **Email**: admin@provesi.com
- **Password**: admin123

### MongoDB:
- Connected to existing MongoDB instance
- Database: `provesi_notifications`
- Collections: `users`, `notifications`

## 🔍 Troubleshooting

### Service not accessible:
1. Check security group allows port 3001
2. Verify instance is running: `terraform output`
3. Check service logs on instance: `pm2 logs notifications`

### Connection issues:
1. Ensure correct public IP: `terraform output notifications_public_ip`
2. Test from AWS console: `curl localhost:3001/health`

### Service not starting:
1. SSH into instance: `ssh ubuntu@<public-ip>`
2. Check PM2 status: `pm2 status`
3. Check logs: `pm2 logs notifications`
4. Restart if needed: `pm2 restart notifications`

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│ Notifications    │───▶│   MongoDB       │
│                 │    │ Service :3001    │    │   Instance      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Email Service  │
                       │   (Optional)     │
                       └──────────────────┘
```

## 📝 Next Steps

1. **Deploy infrastructure**: Run `./deploy_notifications.sh`
2. **Test functionality**: Run `./test_notifications.sh`  
3. **Configure email**: Update `.env` with email credentials (optional)
4. **Monitor service**: Use PM2 dashboard or AWS CloudWatch
5. **Scale if needed**: Increase instance size or add load balancer later