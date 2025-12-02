# API Testing Examples

## Quick Start Commands

### 1. Health Check
```bash
curl -k https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/health
```

### 2. Get JWT Token
```bash
# Store token for reuse
TOKEN=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ProvesiAdmin2024!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

echo "Token: $TOKEN"
```

### 3. Create Test Notification
```bash
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "warning",
    "title": "Inventory Alert",
    "message": "Low stock detected for Product XYZ",
    "priority": "high",
    "targetUser": "gerente@provesi.com"
  }'
```

### 4. List All Notifications
```bash
curl -X GET https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 5. List Unread Notifications Only
```bash
curl -X GET "https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications?read=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Complete Test Scenarios

### Scenario 1: Inventory Management Notifications

```bash
# 1. Low stock alert
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "warning",
    "title": "Low Stock Alert",
    "message": "Product ABC123 has only 5 units remaining in Warehouse A",
    "priority": "high",
    "targetUser": "gerente@provesi.com"
  }'

# 2. Reorder reminder
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "info",
    "title": "Reorder Reminder",
    "message": "Scheduled reorder for Product DEF456 is due tomorrow",
    "priority": "medium",
    "targetUser": "empleado@provesi.com"
  }'

# 3. Order completion
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "success",
    "title": "Order Completed",
    "message": "Order #ORD-2025-001 has been successfully processed and shipped",
    "priority": "low"
  }'
```

### Scenario 2: System Notifications

```bash
# 1. System maintenance
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "info",
    "title": "Scheduled Maintenance",
    "message": "System maintenance scheduled for December 3rd, 2:00 AM - 4:00 AM EST",
    "priority": "medium"
  }'

# 2. Security alert
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "error",
    "title": "Security Alert",
    "message": "Multiple failed login attempts detected for user: empleado",
    "priority": "high",
    "targetUser": "admin@provesi.com"
  }'
```

## User Management Examples

### Create New User via Django

```bash
# This would typically be done through Django admin or custom API
# Example of what the request might look like:

curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/usuarios/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_usuario": "supervisor",
    "email": "supervisor@provesi.com",
    "telefono": "+57 300 555 0123",
    "rol": "gerente"
  }'
```

### Test Authentication for Different Users

```bash
# Test with different user credentials
GERENTE_TOKEN=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "gerente", "password": "Gerente2024!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

EMPLEADO_TOKEN=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "empleado", "password": "Empleado2024!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

echo "Gerente Token: $GERENTE_TOKEN"
echo "Empleado Token: $EMPLEADO_TOKEN"
```

## Performance Testing

### Bulk Notification Creation

```bash
#!/bin/bash
# Create 10 test notifications rapidly

for i in {1..10}; do
  curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"info\",
      \"title\": \"Test Notification $i\",
      \"message\": \"This is test notification number $i for load testing\",
      \"priority\": \"medium\"
    }" &
done

wait
echo "All notifications sent"
```

### Concurrent User Testing

```bash
#!/bin/bash
# Test with multiple users simultaneously

test_user() {
  local username=$1
  local password=$2
  
  # Get token
  local token=$(curl -s -k -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/inventario/auth/login/ \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"password\": \"$password\"}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
  
  # Create notification
  curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"info\",
      \"title\": \"Notification from $username\",
      \"message\": \"Test message from user $username\",
      \"priority\": \"low\"
    }"
}

# Test with all users simultaneously
test_user "admin" "ProvesiAdmin2024!" &
test_user "gerente" "Gerente2024!" &
test_user "empleado" "Empleado2024!" &

wait
echo "Concurrent user test completed"
```

## Error Testing

### Test Invalid Scenarios

```bash
# 1. Test without authentication
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Content-Type: application/json" \
  -d '{"type": "info", "title": "Test", "message": "Should fail"}'

# 2. Test with invalid token
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer invalid_token_here" \
  -H "Content-Type: application/json" \
  -d '{"type": "info", "title": "Test", "message": "Should fail"}'

# 3. Test with malformed JSON
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "info", "title": "Test" // malformed JSON'

# 4. Test with missing required fields
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "info"}' # Missing title and message

# 5. Test invalid notification type
curl -X POST https://provesi-alb-854852274.us-east-1.elb.amazonaws.com/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "invalid_type", "title": "Test", "message": "Invalid type"}'
```

## Response Examples

### Successful Notification Creation
```json
{
  "_id": "6747a1234567890abcdef123",
  "type": "warning",
  "title": "Low Stock Alert",
  "message": "Product ABC123 has only 5 units remaining",
  "priority": "high",
  "isRead": false,
  "createdAt": "2025-12-02T10:30:45.123Z",
  "targetUser": "gerente@provesi.com"
}
```

### Notification List Response
```json
{
  "notifications": [
    {
      "_id": "6747a1234567890abcdef123",
      "type": "warning",
      "title": "Low Stock Alert",
      "message": "Product ABC123 has only 5 units remaining",
      "priority": "high",
      "isRead": false,
      "createdAt": "2025-12-02T10:30:45.123Z"
    },
    {
      "_id": "6747a1234567890abcdef124",
      "type": "success",
      "title": "Order Completed",
      "message": "Order #ORD-2025-001 processed successfully",
      "priority": "low",
      "isRead": true,
      "createdAt": "2025-12-02T09:15:30.456Z",
      "readAt": "2025-12-02T09:20:15.789Z"
    }
  ],
  "total": 25,
  "unread": 8,
  "filtered": 2
}
```

### Error Responses
```json
// 401 Unauthorized
{
  "msg": "No token, authorization denied"
}

// 401 Invalid Token
{
  "msg": "Token is not valid"
}

// 400 Validation Error
{
  "error": "Validation Error",
  "details": {
    "title": "Title is required",
    "message": "Message is required"
  }
}

// 500 Server Error
{
  "error": "Internal Server Error",
  "message": "Database connection failed"
}
```