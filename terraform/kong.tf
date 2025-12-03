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

  user_data = base64encode(<<-EOT
    #!/bin/bash
    exec > /var/log/kong-install.log 2>&1
    set -x
    
    apt-get update
    apt-get install -y docker.io
    systemctl start docker
    systemctl enable docker
    
    mkdir -p /opt/kong
    cat > /opt/kong/kong.yaml << 'EOF'
_format_version: "3.0"
services:
  - name: django-api
    url: https://${aws_lb.main.dns_name}
    routes:
      - name: api-route
        paths: [/api]
        strip_path: false
      - name: inventario-route
        paths: [/inventario]
        strip_path: false
      - name: admin-route
        paths: [/admin]
        strip_path: false
  - name: notifications-service
    url: http://${aws_instance.notifications.private_ip}:8001
    routes:
      - name: notifications-route
        paths: [/notifications]
        strip_path: true
EOF
    
    docker network create kong-net || true
    docker run -d --name kong --restart=always \
      -v /opt/kong:/kong/declarative/ \
      -e KONG_DATABASE=off \
      -e KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yaml \
      -p 8000:8000 \
      kong/kong-gateway
    EOT
  )

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-gateway"
    Role = "api-gateway"
  })

  depends_on = [aws_lb.main, aws_lb_listener.https, aws_instance.app_server, aws_instance.notifications]
}
