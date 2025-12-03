# ==========================================
# KONG API GATEWAY - ÚNICO PUNTO DE ENTRADA
# ==========================================
# Arquitectura:
#   Internet → Kong (Docker) → ALB (interno) → Django Servers
#                           → Notifications (FastAPI)
# ==========================================

# ==========================================
# SECURITY GROUP
# ==========================================

resource "aws_security_group" "kong" {
  name        = "${var.project_prefix}-kong-sg"
  description = "Security group for Kong API Gateway"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP public access"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-sg"
  })
}

# Regla: Permitir que Kong acceda al ALB
resource "aws_security_group_rule" "alb_from_kong" {
  security_group_id        = aws_security_group.alb.id
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access ALB"
}

# ==========================================
# EC2 INSTANCE - KONG WITH DOCKER
# ==========================================

resource "aws_instance" "kong_gateway" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.kong_instance_type
  vpc_security_group_ids      = [aws_security_group.kong.id]
  associate_public_ip_address = true

  user_data = <<-EOT
    #!/bin/bash
    
    # Variables
    ALB_DNS="${aws_lb.main.dns_name}"
    NOTIFICATIONS_IP="${aws_instance.notifications.private_ip}"
    
    # Install Docker
    sudo apt-get update -y
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Create kong.yaml configuration
    sudo mkdir -p /opt/kong
    cat > /opt/kong/kong.yaml << 'KONGCONFIG'
_format_version: "3.0"
_transform: true

services:
  - name: django-api
    url: https://ALB_DNS_PLACEHOLDER
    routes:
      - name: api-route
        paths:
          - /api
        strip_path: false
      - name: inventario-route
        paths:
          - /inventario
        strip_path: false
      - name: admin-route
        paths:
          - /admin
        strip_path: false

  - name: notifications-service
    url: http://NOTIFICATIONS_IP_PLACEHOLDER:8001
    routes:
      - name: notifications-route
        paths:
          - /notifications
        strip_path: true
KONGCONFIG

    # Replace placeholders with actual IPs
    sudo sed -i "s/ALB_DNS_PLACEHOLDER/$ALB_DNS/g" /opt/kong/kong.yaml
    sudo sed -i "s/NOTIFICATIONS_IP_PLACEHOLDER/$NOTIFICATIONS_IP/g" /opt/kong/kong.yaml
    
    # Create Docker network
    sudo docker network create kong-net || true
    
    # Run Kong container
    sudo docker run -d --name kong --network=kong-net --restart=always \
      -v "/opt/kong:/kong/declarative/" \
      -e "KONG_DATABASE=off" \
      -e "KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yaml" \
      -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
      -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
      -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
      -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
      -p 8000:8000 \
      kong/kong-gateway
    
    echo "Kong started with Docker"
    EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-gateway"
    Role = "api-gateway"
  })

  depends_on = [aws_lb.main, aws_lb_listener.https, aws_instance.app_server, aws_instance.notifications]
}
