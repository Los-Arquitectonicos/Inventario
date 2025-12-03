# Independent Notifications Service

A completely independent microservice for managing notifications with email integration, user management, and JWT authentication.

## ✨ Features

- **🔐 Independent Authentication**: Complete JWT-based user management system
- **📧 Email Integration**: Automatic email notifications with HTML templates
- **👥 User Management**: Multi-role system (admin, manager, user)
- **🔒 Security**: Role-based permissions and secure password hashing
- **📊 Comprehensive API**: RESTful endpoints for all operations
- **🚀 Direct Access**: Runs independently on EC2 (not through ALB)

## 🏗️ Architecture

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

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
# Install and start MongoDB
npm run setup  # Creates default users
```

### 4. Start Service
```bash
npm start       # Production
npm run dev     # Development
```

## 📡 API Endpoints

### 🔐 Authentication
```bash
# Login
POST /auth/login
{
  "email": "admin@provesi.com",
  "password": "Admin123!"
}

# Register new user
POST /auth/register
{
  "email": "pedropablost@icloud.com",
  "username": "newuser",
  "firstName": "New",
  "lastName": "User",
  "password": "Password123!"
}

# Get profile
GET /auth/profile
Authorization: Bearer YOUR_JWT_TOKEN
```

### 📬 Notifications
```bash
# Create notification with email
POST /notifications
Authorization: Bearer YOUR_JWT_TOKEN
{
  "title": "Order Update",
  "message": "Your order has been processed",
  "type": "info",
  "priority": "medium",
  "recipientEmail": "user@provesi.com",
  "sendEmail": true
}

# Get notifications (paginated)
GET /notifications?page=1&limit=20&read=false
Authorization: Bearer YOUR_JWT_TOKEN

# Mark as read
PATCH /notifications/:id/read
Authorization: Bearer YOUR_JWT_TOKEN

# Delete notification
DELETE /notifications/:id
Authorization: Bearer YOUR_JWT_TOKEN
```

## 👥 Default Users

| Role    | Email                | Password    | Permissions        |
|---------|---------------------|-------------|--------------------|
| admin   | admin@provesi.com   | Admin123!   | Full system access |
| manager | manager@provesi.com | Manager123! | Create/manage      |
| user    | user@provesi.com    | User123!    | View own only      |

## 🧪 Testing

Run comprehensive tests:
```bash
# Make executable
chmod +x test_independent_service.sh

# Run all tests
./test_independent_service.sh

# Test specific functionality
curl http://your-ec2-ip:3001/health
```

## 📧 Email Configuration

### Gmail Setup
```env
EMAIL_SERVICE=gmail
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password  # Generate in Google Account settings
EMAIL_FROM_NAME=ProvesiWMS Notifications
EMAIL_FROM_ADDRESS=noreply@provesi.com
```

### AWS SES Setup
```env
EMAIL_SERVICE=ses
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
EMAIL_FROM_ADDRESS=verified@yourdomain.com
```

## 🔗 Integration Examples

### Python/Django
```python
import requests

def send_notification(title, message, recipient_email):
    # Get token
    auth_response = requests.post('http://your-ec2-ip:3001/auth/login', {
        'email': 'pedropablost@icloud.com',
        'password': 'Admin123!'
    })
    token = auth_response.json()['token']
    
    # Send notification
    response = requests.post(
        'http://your-ec2-ip:3001/notifications',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': title,
            'message': message,
            'recipientEmail': recipient_email,
            'sendEmail': True
        }
    )
    return response.json()
```

### JavaScript/Frontend
```javascript
class NotificationsAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = null;
  }

  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json();
    if (data.success) this.token = data.token;
    return data;
  }

  async createNotification(notification) {
    return await fetch(`${this.baseURL}/notifications`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(notification)
    }).then(r => r.json());
  }
}
```

## 📊 API Response Examples

### Successful Authentication
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "admin@provesi.com",
    "username": "admin",
    "firstName": "System",
    "lastName": "Administrator",
    "role": "admin"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Notification Creation
```json
{
  "success": true,
  "message": "Notification created successfully",
  "notification": {
    "id": "507f1f77bcf86cd799439012",
    "title": "Order Update",
    "message": "Your order has been processed",
    "type": "info",
    "priority": "medium",
    "recipientEmail": "pedropablost@icloud.com",
    "isRead": false,
    "emailSent": true,
    "emailSentAt": "2024-01-15T10:30:00.000Z",
    "createdAt": "2024-01-15T10:30:00.000Z"
  }
}
```

### Notifications List
```json
{
  "success": true,
  "notifications": [
    {
      "id": "507f1f77bcf86cd799439012",
      "title": "Order Update",
      "message": "Your order has been processed",
      "type": "info",
      "priority": "medium",
      "recipientEmail": "pedropablost@icloud.com",
      "isRead": false,
      "emailSent": true,
      "sender": {
        "name": "System Administrator",
        "email": "pedropablost@icloud.com",
        "role": "admin"
      },
      "createdAt": "2024-01-15T10:30:00.000Z"
    }
  ],
  "pagination": {
    "current": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  },
  "summary": {
    "total": 1,
    "unread": 1,
    "filtered": 1
  }
}
```

## 🔧 Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## 🎯 Service URLs

- **Health Check**: `http://your-ec2-ip:3001/health`
- **API Base**: `http://your-ec2-ip:3001`
- **Authentication**: `http://your-ec2-ip:3001/auth/*`
- **Notifications**: `http://your-ec2-ip:3001/notifications`

## 🔍 Monitoring

```bash
# Health check
curl http://your-ec2-ip:3001/health

# Service status
pm2 status

# View logs
pm2 logs notifications-service

# Database stats
mongo notifications --eval "
  print('Users:', db.users.count());
  print('Notifications:', db.notifications.count());
"
```

## 📝 Notes

- **Independent Service**: Does not depend on Django/ALB infrastructure
- **Direct Access**: Accessible directly via EC2 IP and port 3001
- **Scalable**: Can be horizontally scaled with load balancers
- **Secure**: JWT-based authentication with bcrypt password hashing
- **Email Ready**: Professional HTML email templates included

This service provides a complete, production-ready notifications solution that can integrate with any application stack while maintaining independence and security.
    password='Supervisor2024!',
    first_name='Carlos',
    last_name='Supervisor',
    telefono='+57 300 555 0123',
    rol='gerente'
)
```

### 3. User Roles and Permissions

| Role | Description | Notification Access |
|------|-------------|-------------------|
| `admin` | Full system access | All notifications |
| `gerente` | Manager level | Department notifications |
| `empleado` | Employee level | Personal notifications |

## Email Integration

The notifications service automatically sends emails when notifications are created with `sendEmail: true`. Email configuration:

### 1. Email Service Setup

Add email service configuration to the Node.js service:

```javascript
// src/config/email.js
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransporter({
  service: 'gmail', // or AWS SES
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASSWORD
  }
});

module.exports = transporter;
```

### 2. Email Templates

Create email templates for different notification types:

```javascript
// src/templates/emailTemplates.js
const templates = {
  lowStock: {
    subject: '⚠️ Low Stock Alert - {{productName}}',
    html: `
      <h2>Low Stock Alert</h2>
      <p>Product: <strong>{{productName}}</strong></p>
      <p>Current Stock: <strong>{{currentStock}}</strong></p>
      <p>Please reorder soon to avoid stockouts.</p>
    `
  },
  orderComplete: {
    subject: '✅ Order Completed - #{{orderNumber}}',
    html: `
      <h2>Order Completed</h2>
      <p>Order #{{orderNumber}} has been processed successfully.</p>
      <p>Thank you for your business!</p>
    `
  }
};
```

### 3. Environment Variables for Email

Add to your deployment configuration:

```bash
# Email Configuration
EMAIL_USER=notifications@provesi.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM="ProvesiWMS <notifications@provesi.com>"
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

## Testing

### Complete Test Script

Use the provided test script to verify all functionality:

```bash
# Make executable
chmod +x ProvesiWMS/test_notifications.sh

# Run tests
./ProvesiWMS/test_notifications.sh
```

### Manual Testing Steps

1. **Health Check:**
```bash
curl -k https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/health
```

2. **Authenticate:**
```bash
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ProvesiAdmin2024!"}'
```

3. **Create Notification:**
```bash
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "info", "title": "Test", "message": "Test message"}'
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Service is down or not responding
   - Check EC2 instance status
   - Verify MongoDB connection
   - Check PM2 process: `pm2 status`

2. **401 Unauthorized**: Invalid or expired token
   - Re-authenticate to get new token
   - Verify token format in Authorization header

3. **500 Internal Server Error**: Server-side error
   - Check application logs: `pm2 logs notifications`
   - Verify MongoDB connection
   - Check environment variables

### Log Monitoring

```bash
# SSH to notifications server
ssh ubuntu@3.238.232.34

# Check PM2 status
pm2 status

# View logs
pm2 logs notifications

# Restart service if needed
pm2 restart notifications
```

## Security Considerations

1. **JWT Token Security**: Tokens expire based on Django configuration
2. **HTTPS Only**: All communication should use HTTPS
3. **CORS Configuration**: Properly configured for allowed origins
4. **Input Validation**: All inputs are validated before processing
5. **Rate Limiting**: Consider implementing rate limiting for production

## Future Enhancements

1. **Real-time Notifications**: WebSocket integration
2. **Email Notifications**: SMTP integration
3. **Push Notifications**: Mobile app integration
4. **Notification Preferences**: User-configurable notification settings
5. **Analytics**: Notification delivery and read statistics

---

**Last Updated**: December 2, 2025  
**Version**: 1.0.0  
**Contact**: admin@provesi.com