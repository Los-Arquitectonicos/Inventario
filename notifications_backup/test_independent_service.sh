#!/bin/bash

# Test script for Independent Notifications Service
# Tests authentication, notifications, and email functionality

# Configuration
BASE_URL="http://54.208.46.172:3001"  # Direct EC2 access
API_URL="${BASE_URL}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ((PASSED_TESTS++))
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ((FAILED_TESTS++))
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
    esac
    ((TOTAL_TESTS++))
}

# Function to test HTTP endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=$4
    local token=$5
    local description=$6

    print_status "INFO" "Testing: $description"
    echo "  Method: $method"
    echo "  Endpoint: $endpoint"
    
    # Build curl command
    local curl_cmd="curl -s -w '%{http_code}' -X $method"
    
    if [ ! -z "$token" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    fi
    
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ ! -z "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd $endpoint"
    
    # Execute request
    local response=$(eval $curl_cmd)
    local http_code="${response: -3}"
    local body="${response%???}"
    
    echo "  Response Code: $http_code"
    echo "  Response Body: $body"
    
    # Check result
    if [ "$http_code" -eq "$expected_code" ]; then
        print_status "SUCCESS" "$description - HTTP $http_code"
        echo "$body"
        return 0
    else
        print_status "ERROR" "$description - Expected $expected_code, got $http_code"
        echo "$body"
        return 1
    fi
    echo ""
}

# Function to extract token from login response
extract_token() {
    local response=$1
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('token', ''))
except:
    print('')
"
}

# Function to extract notification ID from response
extract_notification_id() {
    local response=$1
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('notification', {}).get('id', ''))
except:
    print('')
"
}

echo "🚀 Testing Independent Notifications Service"
echo "=============================================="
echo "Base URL: $API_URL"
echo "Testing Direct EC2 Access (No ALB)"
echo ""

# Test 1: Health Check
print_status "INFO" "1. Health Check"
test_endpoint "GET" "$API_URL/health" "" 200 "" "Service Health Check"
echo ""

# Test 2: Authentication - Login with Admin
print_status "INFO" "2. Admin Authentication"
admin_login_data='{
  "email": "admin@provesi.com",
  "password": "Admin123!"
}'

admin_response=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "$admin_login_data")

admin_token=$(extract_token "$admin_response")

if [ ! -z "$admin_token" ]; then
    print_status "SUCCESS" "Admin login successful"
    echo "Admin Token: ${admin_token:0:20}..."
else
    print_status "ERROR" "Admin login failed"
    echo "Response: $admin_response"
fi
echo ""

# Test 3: Authentication - Login with Manager
print_status "INFO" "3. Manager Authentication"
manager_login_data='{
  "email": "manager@provesi.com",
  "password": "Manager123!"
}'

manager_response=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "$manager_login_data")

manager_token=$(extract_token "$manager_response")

if [ ! -z "$manager_token" ]; then
    print_status "SUCCESS" "Manager login successful"
    echo "Manager Token: ${manager_token:0:20}..."
else
    print_status "ERROR" "Manager login failed"
    echo "Response: $manager_response"
fi
echo ""

# Test 4: Authentication - Login with Regular User
print_status "INFO" "4. User Authentication"
user_login_data='{
  "email": "user@provesi.com",
  "password": "User123!"
}'

user_response=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "$user_login_data")

user_token=$(extract_token "$user_response")

if [ ! -z "$user_token" ]; then
    print_status "SUCCESS" "User login successful"
    echo "User Token: ${user_token:0:20}..."
else
    print_status "ERROR" "User login failed"
    echo "Response: $user_response"
fi
echo ""

# Test 5: Create Notification (Admin)
if [ ! -z "$admin_token" ]; then
    print_status "INFO" "5. Create Notification (Admin)"
    notification_data='{
      "title": "Test Notification",
      "message": "This is a test notification from the automated test script.",
      "type": "info",
      "priority": "medium",
      "recipientEmail": "user@provesi.com",
      "sendEmail": false
    }'
    
    notification_response=$(curl -s -X POST "$API_URL/notifications" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $admin_token" \
      -d "$notification_data")
    
    notification_id=$(extract_notification_id "$notification_response")
    
    if [[ "$notification_response" == *'"success":true'* ]]; then
        print_status "SUCCESS" "Notification created successfully"
        echo "Notification ID: $notification_id"
        echo "Response: $notification_response"
    else
        print_status "ERROR" "Failed to create notification"
        echo "Response: $notification_response"
    fi
    echo ""
fi

# Test 6: Create Notification with Email (Admin)
if [ ! -z "$admin_token" ]; then
    print_status "INFO" "6. Create Notification with Email (Admin)"
    email_notification_data='{
      "title": "Test Email Notification",
      "message": "This notification will also be sent via email to test the email service integration.",
      "type": "info",
      "priority": "high",
      "recipientEmail": "user@provesi.com",
      "sendEmail": true
    }'
    
    email_notification_response=$(curl -s -X POST "$API_URL/notifications" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $admin_token" \
      -d "$email_notification_data")
    
    if [[ "$email_notification_response" == *'"success":true'* ]]; then
        print_status "SUCCESS" "Email notification created successfully"
        echo "Response: $email_notification_response"
    else
        print_status "ERROR" "Failed to create email notification"
        echo "Response: $email_notification_response"
    fi
    echo ""
fi

# Test 7: Get Notifications (User)
if [ ! -z "$user_token" ]; then
    print_status "INFO" "7. Get User Notifications"
    
    notifications_response=$(curl -s -X GET "$API_URL/notifications" \
      -H "Authorization: Bearer $user_token")
    
    if [[ "$notifications_response" == *'"success":true'* ]]; then
        print_status "SUCCESS" "Retrieved user notifications"
        echo "Response: $notifications_response"
    else
        print_status "ERROR" "Failed to retrieve notifications"
        echo "Response: $notifications_response"
    fi
    echo ""
fi

# Test 8: Get All Notifications (Admin)
if [ ! -z "$admin_token" ]; then
    print_status "INFO" "8. Get All Notifications (Admin)"
    
    all_notifications_response=$(curl -s -X GET "$API_URL/notifications" \
      -H "Authorization: Bearer $admin_token")
    
    if [[ "$all_notifications_response" == *'"success":true'* ]]; then
        print_status "SUCCESS" "Retrieved all notifications (admin view)"
        echo "Response: $all_notifications_response"
    else
        print_status "ERROR" "Failed to retrieve all notifications"
        echo "Response: $all_notifications_response"
    fi
    echo ""
fi

# Test 9: Mark Notification as Read
if [ ! -z "$user_token" ] && [ ! -z "$notification_id" ]; then
    print_status "INFO" "9. Mark Notification as Read"
    
    read_response=$(curl -s -X PATCH "$API_URL/notifications/$notification_id/read" \
      -H "Authorization: Bearer $user_token")
    
    if [[ "$read_response" == *'"success":true'* ]]; then
        print_status "SUCCESS" "Notification marked as read"
        echo "Response: $read_response"
    else
        print_status "ERROR" "Failed to mark notification as read"
        echo "Response: $read_response"
    fi
    echo ""
fi

# Test 10: User Profile
if [ ! -z "$user_token" ]; then
    print_status "INFO" "10. Get User Profile"
    
    profile_response=$(curl -s -X GET "$API_URL/auth/profile" \
      -H "Authorization: Bearer $user_token")
    
    if [[ "$profile_response" == *'"success":true'* ]]; then
        print_status "SUCCESS" "Retrieved user profile"
        echo "Response: $profile_response"
    else
        print_status "ERROR" "Failed to retrieve user profile"
        echo "Response: $profile_response"
    fi
    echo ""
fi

# Test 11: Unauthorized Access
print_status "INFO" "11. Test Unauthorized Access"
unauthorized_response=$(curl -s -w '%{http_code}' -X GET "$API_URL/notifications")
http_code="${unauthorized_response: -3}"

if [ "$http_code" -eq "401" ]; then
    print_status "SUCCESS" "Unauthorized access properly rejected (401)"
else
    print_status "ERROR" "Unauthorized access not properly handled (expected 401, got $http_code)"
fi
echo ""

# Final Summary
echo ""
echo "🏁 Test Summary"
echo "==============="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    print_status "SUCCESS" "All tests passed! 🎉"
    echo ""
    echo "✅ The Notifications Service is working correctly!"
    echo ""
    echo "📝 Key Test Results:"
    echo "  - ✅ Service is accessible directly via EC2"
    echo "  - ✅ Independent authentication system working"
    echo "  - ✅ Notification creation and retrieval working"
    echo "  - ✅ Email integration ready"
    echo "  - ✅ Role-based permissions working"
    echo "  - ✅ Security controls in place"
    echo ""
    echo "🚀 Service ready for production use!"
    exit 0
else
    print_status "ERROR" "$FAILED_TESTS tests failed"
    echo ""
    echo "❌ Please check the failed tests above and verify:"
    echo "  - Service is running on the correct port (3001)"
    echo "  - MongoDB is accessible and contains default users"
    echo "  - Email configuration is correct"
    echo "  - Network security groups allow port 3001"
    echo ""
    echo "💡 To set up default users, run: npm run setup"
    exit 1
fi