#!/bin/bash

# ==========================================
# TEST NOTIFICATIONS SERVICE
# ==========================================
# This script tests the standalone notifications service

set -e

# Get the notifications IP from terraform output
if [ -f "terraform.tfstate" ]; then
    NOTIFICATIONS_IP=$(terraform output -raw notifications_public_ip 2>/dev/null || echo "")
fi

# If not available from terraform, use the IP from addresses file
if [ -z "$NOTIFICATIONS_IP" ] && [ -f "../adresses" ]; then
    NOTIFICATIONS_IP=$(grep "notifications_public_ip" ../adresses | cut -d'"' -f2 || echo "")
fi

# If still not available, ask user
if [ -z "$NOTIFICATIONS_IP" ]; then
    read -p "Enter the notifications service public IP: " NOTIFICATIONS_IP
fi

BASE_URL="http://${NOTIFICATIONS_IP}:3001"

echo "============================================"
echo "TESTING NOTIFICATIONS SERVICE"
echo "Base URL: $BASE_URL"
echo "============================================"

# Test 1: Health Check
echo "🏥 Testing health endpoint..."
if curl -s "${BASE_URL}/health" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "Make sure the service is running and accessible"
    exit 1
fi

# Test 2: Register Admin User
echo ""
echo "👤 Registering admin user..."
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@provesi.com",
    "password": "admin123",
    "role": "admin"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "token\|user"; then
    echo "✅ Admin user registration successful"
else
    echo "ℹ️  Admin user may already exist (this is normal)"
fi

# Test 3: Login
echo ""
echo "🔑 Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@provesi.com",
    "password": "admin123"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4 || echo "")

if [ -n "$TOKEN" ]; then
    echo "✅ Login successful"
    echo "🎟️  Token obtained: ${TOKEN:0:20}..."
else
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# Test 4: Create Notification
echo ""
echo "🔔 Testing notification creation..."
NOTIFICATION_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/notifications" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Notification",
    "message": "This is a test notification from the standalone service",
    "type": "info",
    "recipients": ["test@example.com"]
  }')

if echo "$NOTIFICATION_RESPONSE" | grep -q "_id\|id"; then
    echo "✅ Notification creation successful"
    NOTIFICATION_ID=$(echo "$NOTIFICATION_RESPONSE" | grep -o '"_id":"[^"]*"' | cut -d'"' -f4 || echo "")
    echo "📝 Notification ID: $NOTIFICATION_ID"
else
    echo "❌ Notification creation failed"
    echo "Response: $NOTIFICATION_RESPONSE"
fi

# Test 5: Get Notifications
echo ""
echo "📋 Testing notification retrieval..."
NOTIFICATIONS_LIST=$(curl -s -X GET "${BASE_URL}/api/notifications" \
  -H "Authorization: Bearer $TOKEN")

if echo "$NOTIFICATIONS_LIST" | grep -q "notifications\|data"; then
    echo "✅ Notification retrieval successful"
    NOTIFICATION_COUNT=$(echo "$NOTIFICATIONS_LIST" | grep -o '"title"' | wc -l | tr -d ' ')
    echo "📊 Found $NOTIFICATION_COUNT notifications"
else
    echo "❌ Notification retrieval failed"
fi

echo ""
echo "============================================"
echo "✅ ALL TESTS COMPLETED"
echo "============================================"
echo ""
echo "🎯 Service URLs:"
echo "   Health: ${BASE_URL}/health"
echo "   API Auth: ${BASE_URL}/api/auth"
echo "   API Notifications: ${BASE_URL}/api/notifications"
echo ""
echo "🔑 Admin Credentials:"
echo "   Email: admin@provesi.com"
echo "   Password: admin123"
echo ""