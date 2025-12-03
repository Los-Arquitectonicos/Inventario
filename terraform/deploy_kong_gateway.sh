#!/bin/bash

# ==========================================
# DEPLOY KONG API GATEWAY
# ==========================================
# This script deploys Kong as a centralized API Gateway

set -e

echo "============================================"
echo "🦍 DEPLOYING KONG API GATEWAY"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo "Error: Please run this script from the terraform directory"
    echo "cd /path/to/Inventario/ProvesiWMS/terraform"
    exit 1
fi

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
fi

# Validate the configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Plan the deployment
echo "📋 Planning Kong deployment..."
terraform plan -out=kong-deployment.tfplan

echo ""
echo "🦍 KONG IMPLEMENTATION OVERVIEW:"
echo "   ✅ Kong Gateway as centralized API Gateway"
echo "   ✅ All traffic routes through Kong (ALB → Kong → Services)"
echo "   ✅ Direct access to Kong for testing: http://<kong-ip>:8000"
echo "   ✅ Services: Django API + Notifications"
echo "   ✅ Future services can be easily added"
echo ""
echo "🔀 ROUTING:"
echo "   /api/* → Django Backend"
echo "   /inventario/* → Django Backend"
echo "   /admin/* → Django Backend"
echo "   /notifications/* → Notifications Service"
echo ""
echo "⚠️  IMPORTANT CHANGES:"
echo "   - All ALB traffic now routes to Kong first"
echo "   - Kong then routes to appropriate backend services"
echo "   - Notifications service still accessible directly for testing"
echo "   - Kong Admin API available via SSH tunnel only"
echo ""

read -p "Continue with Kong deployment? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply the changes
echo "🚀 Deploying Kong Gateway..."
terraform apply kong-deployment.tfplan

# Get outputs
echo ""
echo "============================================"
echo "🦍 KONG DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "📊 Getting deployment information..."
terraform output

echo ""
echo "🦍 KONG GATEWAY INFO:"
KONG_IP=$(terraform output -raw kong_gateway_public_ip 2>/dev/null || echo "pending...")
ALB_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "pending...")

echo "   Kong Direct URL: http://$KONG_IP:8000"
echo "   API Gateway URL: $ALB_URL"
echo "   Kong Admin SSH: ssh ubuntu@$KONG_IP"
echo ""
echo "🧪 TEST COMMANDS:"
echo ""
echo "   # Test Kong directly"
echo "   curl http://$KONG_IP:8000/"
echo ""
echo "   # Test via ALB (recommended)"
echo "   curl $ALB_URL/api/"
echo "   curl $ALB_URL/notifications/"
echo ""
echo "   # Access Kong Admin API (via SSH tunnel)"
echo "   ssh -L 8001:localhost:8001 ubuntu@$KONG_IP"
echo "   # Then in another terminal:"
echo "   curl http://localhost:8001/services"
echo ""
echo "📚 NEXT STEPS:"
echo "   1. Test Kong routing: ./test_kong_gateway.sh"
echo "   2. Configure JWT authentication in Kong"
echo "   3. Add additional microservices to Kong configuration"
echo "   4. Set up monitoring and logging"
echo ""
echo "✅ Kong Gateway deployed successfully!"

# Create a simple test script
cat > test_kong_gateway.sh << 'EOF'
#!/bin/bash

echo "🦍 Testing Kong Gateway..."

# Get Kong IP from terraform
if [ -f "terraform.tfstate" ]; then
    KONG_IP=$(terraform output -raw kong_gateway_public_ip 2>/dev/null)
    ALB_URL=$(terraform output -raw api_gateway_url 2>/dev/null)
else
    read -p "Enter Kong Gateway IP: " KONG_IP
    read -p "Enter ALB URL: " ALB_URL
fi

echo "Kong IP: $KONG_IP"
echo "ALB URL: $ALB_URL"

# Test Kong health
echo ""
echo "🔍 Testing Kong health (direct)..."
if curl -s "http://$KONG_IP:8000/" | grep -q "Kong"; then
    echo "✅ Kong is responding"
else
    echo "❌ Kong is not responding directly"
fi

# Test via ALB
echo ""
echo "🔍 Testing Kong via ALB..."
if curl -s "$ALB_URL/" -o /dev/null; then
    echo "✅ Kong accessible via ALB"
else
    echo "❌ Kong not accessible via ALB"
fi

echo ""
echo "🦍 Kong Gateway test complete!"
EOF

chmod +x test_kong_gateway.sh
echo ""
echo "💡 Test script created: ./test_kong_gateway.sh"