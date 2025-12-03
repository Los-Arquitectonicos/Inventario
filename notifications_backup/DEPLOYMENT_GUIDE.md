# Notifications Service - Independent Deployment Guide

## Overview

The Notifications Service is now a completely independent microservice with its own:
- User management system
- Authentication (JWT-based)
- MongoDB database
- Email integration
- Direct EC2 access (not through ALB)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client Apps   │────▶│  EC2:3001        │────▶│   MongoDB       │
│                 │     │  (Direct Access) │     │  (Independent)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Email Service   │
                        │  (Nodemailer)    │
                        └──────────────────┘
```

## Deployment Steps

### 1. Server Setup

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Navigate to notifications directory
cd /path/to/notifications

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
nano .env
```

### 2. Environment Configuration

Create `.env` file:

```env
# Server Configuration
PORT=3001
NODE_ENV=production

# MongoDB (Independent Database)
MONGO_URI=mongodb://localhost:27017/notifications

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-here

# Email Configuration (Gmail example)
EMAIL_SERVICE=gmail
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
EMAIL_FROM_NAME=ProvesiWMS Notifications
EMAIL_FROM_ADDRESS=noreply@provesi.com

# Optional: Custom email templates
EMAIL_TEMPLATE_DIR=./src/templates/email
```

### 3. Database Setup

```bash
# Install MongoDB if not already installed
sudo yum install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create default users
npm run setup
```

### 4. Security Groups

Ensure your EC2 security group allows:
- **Inbound**: Port 3001 from your application sources
- **Outbound**: Port 587 (SMTP) for email sending
- **Outbound**: Port 27017 (MongoDB)

### 5. Start Service

```bash
# Production start
npm start

# Or with PM2 for process management
npm install -g pm2
pm2 start server.js --name "notifications-service"
pm2 save
pm2 startup
```

## API Endpoints

### Authentication

```bash
# Login
curl -X POST http://your-ec2-ip:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@provesi.com",
    "password": "Admin123!"
  }'

# Get Profile
curl -X GET http://your-ec2-ip:3001/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Notifications

```bash
# Create Notification
curl -X POST http://your-ec2-ip:3001/notifications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Order Update",
    "message": "Your order has been processed",
    "type": "info",
    "priority": "medium",
    "recipientEmail": "user@provesi.com",
    "sendEmail": true
  }'

# Get Notifications
curl -X GET http://your-ec2-ip:3001/notifications \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Mark as Read
curl -X PATCH http://your-ec2-ip:3001/notifications/NOTIFICATION_ID/read \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Default Users

After running `npm run setup`, these users are available:

| Role    | Email                | Password    | Description        |
|---------|---------------------|-------------|--------------------|
| admin   | admin@provesi.com   | Admin123!   | Full system access |
| manager | manager@provesi.com | Manager123! | Can create/manage  |
| user    | user@provesi.com    | User123!    | Can view own       |

## Email Configuration

### Gmail Setup

1. Enable 2-factor authentication on your Gmail account
2. Generate an app password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use this app password in `EMAIL_PASS`

### AWS SES Setup

```env
EMAIL_SERVICE=ses
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
EMAIL_FROM_ADDRESS=verified@yourdomain.com
```

## Integration with Main Application

### Django Integration

```python
import requests
import json

# Get JWT token
def get_notifications_token():
    response = requests.post('http://your-ec2-ip:3001/auth/login', {
        'email': 'admin@provesi.com',
        'password': 'Admin123!'
    })
    return response.json().get('token')

# Send notification
def send_notification(title, message, recipient_email, send_email=True):
    token = get_notifications_token()
    
    response = requests.post(
        'http://your-ec2-ip:3001/notifications',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            'title': title,
            'message': message,
            'recipientEmail': recipient_email,
            'sendEmail': send_email,
            'type': 'info',
            'priority': 'medium'
        }
    )
    
    return response.json()
```

### JavaScript/Frontend Integration

```javascript
class NotificationsAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    if (data.success) {
      this.token = data.token;
    }
    return data;
  }

  async createNotification(notification) {
    const response = await fetch(`${this.baseURL}/notifications`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(notification)
    });
    
    return await response.json();
  }

  async getNotifications() {
    const response = await fetch(`${this.baseURL}/notifications`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    return await response.json();
  }
}

// Usage
const notificationsAPI = new NotificationsAPI('http://your-ec2-ip:3001');
await notificationsAPI.login('admin@provesi.com', 'Admin123!');
await notificationsAPI.createNotification({
  title: 'Test',
  message: 'Hello World',
  recipientEmail: 'user@example.com',
  sendEmail: true
});
```

## Testing

Run comprehensive tests:

```bash
# Make test script executable
chmod +x test_independent_service.sh

# Run tests
./test_independent_service.sh
```

## Monitoring

### Health Check

```bash
curl http://your-ec2-ip:3001/health
```

### Logs

```bash
# View logs with PM2
pm2 logs notifications-service

# Or check log files
tail -f /path/to/logs/notifications.log
```

### Database Stats

```bash
# Connect to MongoDB
mongo notifications

# Check collections
db.users.count()
db.notifications.count()

# Recent notifications
db.notifications.find().sort({createdAt: -1}).limit(5)
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Service not running on port 3001
   ```bash
   pm2 restart notifications-service
   ```

2. **Authentication Failed**: Check JWT secret and user credentials
   ```bash
   npm run setup  # Recreate default users
   ```

3. **Email Not Sending**: Check email configuration
   ```bash
   # Test email config
   node -e "
   require('dotenv').config();
   console.log('EMAIL_USER:', process.env.EMAIL_USER);
   console.log('EMAIL_SERVICE:', process.env.EMAIL_SERVICE);
   "
   ```

4. **Database Connection**: Check MongoDB status
   ```bash
   sudo systemctl status mongod
   ```

### Performance Tuning

1. **Database Indexing**:
   ```javascript
   // Connect to MongoDB and add indexes
   db.notifications.createIndex({ recipientEmail: 1, createdAt: -1 })
   db.notifications.createIndex({ isRead: 1 })
   db.users.createIndex({ email: 1 }, { unique: true })
   ```

2. **Memory Usage**:
   ```bash
   # Monitor with PM2
   pm2 monit
   ```

## Backup

```bash
# Backup MongoDB
mongodump --db notifications --out /backup/notifications-$(date +%Y%m%d)

# Restore if needed
mongorestore --db notifications /backup/notifications-YYYYMMDD/notifications
```

This independent architecture ensures the notifications service can operate completely separately from your main Django application while providing all the necessary functionality for user management, authentication, notifications, and email integration.