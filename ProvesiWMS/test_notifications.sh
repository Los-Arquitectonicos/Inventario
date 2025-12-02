#!/bin/bash

# Configuration
BASE_URL="https://provesi-alb-854852274.us-east-1.elb.amazonaws.com"
NOTIFICATIONS_URL="${BASE_URL}/api/notifications"
AUTH_URL="${BASE_URL}/inventario/auth/login/"
HEALTH_URL="${BASE_URL}/health"

# Credentials (from user_credentials attachment)
USERNAME="admin"
PASSWORD="ProvesiAdmin2024!"

echo "=================================================="
echo "Testing Notifications Service on AWS"
echo "Base URL: ${BASE_URL}"
echo "=================================================="

# 0. Health Check
echo -e "\n[0] Checking notifications service health..."
HEALTH_RESPONSE=$(curl -s -k "${HEALTH_URL}")
echo "Health Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Service is healthy"
else
    echo "⚠️  Service health check failed"
fi

# 1. Authenticate to get JWT Token
echo -e "\n[1] Authenticating as ${USERNAME}..."
LOGIN_RESPONSE=$(curl -s -k -X POST "${AUTH_URL}" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}")

echo "Login Response: $LOGIN_RESPONSE"

# Extract Token (assuming response contains { "access": "..." } or similar)
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Authentication Failed!"
  echo "Trying to extract token differently..."
  # Try alternative extraction methods
  TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access', ''))" 2>/dev/null)
fi

if [ -z "$TOKEN" ]; then
  echo "❌ Could not extract token. Exiting."
  exit 1
fi

echo "✅ Authenticated! Token: ${TOKEN:0:20}..."

# 2. Create a Notification
echo -e "\n[2] Creating a new notification..."
CREATE_RESPONSE=$(curl -s -k -X POST "${NOTIFICATIONS_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "info",
    "title": "Test Notification from CURL",
    "message": "This is a test notification created via script.",
    "priority": "high"
  }')

echo "Create Response: $CREATE_RESPONSE"
NOTIF_ID=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('_id', data.get('id', '')))" 2>/dev/null)

if [ -z "$NOTIF_ID" ]; then
    echo "❌ Failed to create notification"
    echo "Checking if there's an error message..."
    echo $CREATE_RESPONSE | python3 -m json.tool 2>/dev/null || echo "Invalid JSON response"
else
    echo "✅ Notification Created! ID: $NOTIF_ID"
fi

# 3. List Notifications
echo -e "\n[3] Listing notifications..."
LIST_RESPONSE=$(curl -s -k -X GET "${NOTIFICATIONS_URL}" \
  -H "Authorization: Bearer ${TOKEN}")

echo "List Response:"
echo $LIST_RESPONSE | python3 -m json.tool 2>/dev/null || echo "Raw response: $LIST_RESPONSE"

# 4. Mark as Read (if ID exists)
if [ ! -z "$NOTIF_ID" ]; then
    echo -e "\n[4] Marking notification $NOTIF_ID as read..."
    READ_RESPONSE=$(curl -s -k -X PATCH "${NOTIFICATIONS_URL}/${NOTIF_ID}/read" \
      -H "Authorization: Bearer ${TOKEN}")
      
    echo "Read Response: $READ_RESPONSE"
    echo "✅ Marked as read."
fi

# 5. Delete Notification (if ID exists)
if [ ! -z "$NOTIF_ID" ]; then
    echo -e "\n[5] Deleting notification $NOTIF_ID..."
    DELETE_RESPONSE=$(curl -s -k -X DELETE "${NOTIFICATIONS_URL}/${NOTIF_ID}" \
      -H "Authorization: Bearer ${TOKEN}")
      
    echo "Delete Response: $DELETE_RESPONSE"
    echo "✅ Deleted."
fi

echo -e "\n=================================================="
echo "Test Complete"
echo "=================================================="
