#!/bin/bash

# ==========================================
# DEPLOY NOTIFICATIONS SERVICE - STANDALONE
# ==========================================
# This script deploys the updated infrastructure with 
# the notifications service running independently

set -e

echo "============================================"
echo "DEPLOYING NOTIFICATIONS SERVICE (STANDALONE)"
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
echo "📋 Planning deployment..."
terraform plan -out=deployment.tfplan

echo ""
echo "⚠️  IMPORTANT CHANGES:"
echo "   - Notifications service will be accessible directly on port 3001"
echo "   - No longer routed through ALB"
echo "   - Direct access: http://<public-ip>:3001"
echo "   - Security group updated to allow public access on port 3001"
echo ""

read -p "Continue with deployment? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply the changes
echo "🚀 Deploying infrastructure..."
terraform apply deployment.tfplan

# Get outputs
echo ""
echo "============================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "📊 Getting deployment information..."
terraform output

echo ""
echo "🔔 NOTIFICATIONS SERVICE INFO:"
echo "   Direct URL: http://$(terraform output -raw notifications_public_ip):3001"
echo "   Health Check: http://$(terraform output -raw notifications_public_ip):3001/health"
echo "   API Base: http://$(terraform output -raw notifications_public_ip):3001/api"
echo ""
echo "🧪 TEST COMMANDS:"
echo "   curl http://$(terraform output -raw notifications_public_ip):3001/health"
echo ""
echo "✅ Deployment completed successfully!"