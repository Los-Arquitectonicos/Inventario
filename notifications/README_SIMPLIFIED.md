# Notifications Service - Simplified for Testing

## ⚡ Quick Overview

This is a **simplified version** of the notifications service designed specifically for **Kong API Gateway routing testing**. The original full-featured version has been backed up to `../notifications_backup/`.

## 🎯 Purpose

- **Validate Kong routing** from ALB → Kong → Backend Services
- **Test infrastructure** before deploying complex services  
- **Confirm network connectivity** between components
- **Simple GET endpoint testing** for CI/CD pipelines

## 📋 Available Endpoints

| Endpoint | Method | Purpose |
|----------|---------|----------|
| `/` | GET | Root endpoint with service info |
| `/health` | GET | Health check (for ALB health checks) |
| `/test` | GET | Routing validation endpoint |

## 🚀 Quick Test Locally

```bash
# Start the service
npm start
# or
node server.js

# Test endpoints
curl http://localhost:3001/health
curl http://localhost:3001/test
curl http://localhost:3001/
```

## 📁 What's Simplified

### ✅ Kept (Essential for testing)
- Express.js server
- CORS configuration  
- Health check endpoint
- Basic JSON responses
- Logging for debugging

### ❌ Removed (Complex features)
- MongoDB database connection
- JWT authentication
- User management
- Email notifications  
- Complex business logic
- Background jobs

## 🔄 Routing Through Kong

When deployed, requests flow like this:

```
Internet → ALB → Kong Gateway → Notifications Service
```

Kong configuration routes these paths to notifications:
- `/notifications/*` → Notifications Service (port 3001)
- `/api/notifications/*` → Notifications Service (port 3001)

## 🛠 Infrastructure Testing

Use the routing test script:

```bash
# From terraform directory
./test_routing.sh

# Or with specific ALB DNS
./test_routing.sh your-alb-dns.amazonaws.com
```

## 📦 Dependencies

Minimal dependencies for maximum reliability:

```json
{
  "express": "^4.18.2",
  "cors": "^2.8.5", 
  "dotenv": "^16.3.1"
}
```

## 🔄 Restore Full Version

To restore the complete notifications service:

```bash
# Remove simplified version
rm -rf notifications/

# Restore from backup
cp -r notifications_backup/ notifications/
cd notifications/
npm install
```

## 🌍 Environment Variables

```bash
PORT=3001              # Server port
HOST=0.0.0.0          # Bind to all interfaces  
NODE_ENV=testing      # Environment
SERVICE_NAME=notifications-simple
SERVICE_VERSION=1.0.0-simple
```

## ✅ Success Criteria

The service is working correctly when:

1. **Local Testing**: `curl http://localhost:3001/health` returns 200 OK
2. **Kong Routing**: `curl http://alb-dns/notifications/health` returns 200 OK
3. **Logs**: Service logs show incoming requests with timestamps
4. **JSON Response**: All endpoints return valid JSON

## 🎯 Next Steps

After routing validation:

1. **Confirm Kong routing works** ✅
2. **Deploy Django API services** 
3. **Enable JWT authentication** in Kong
4. **Restore full notifications service**
5. **Add monitoring and alerting**

---

**Note**: This simplified version is intentionally minimal for testing. Restore the full version from `notifications_backup/` for production use.