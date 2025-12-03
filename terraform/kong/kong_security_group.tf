# ==========================================
# KONG API GATEWAY - SECURITY GROUP
# ==========================================

resource "aws_security_group" "kong" {
  name        = "${var.project_prefix}-kong-sg"
  description = "Security group for Kong API Gateway"
  vpc_id      = data.aws_vpc.default.id
  
  # Proxy HTTP desde ALB
  ingress {
    description     = "Kong proxy from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Proxy HTTPS desde ALB (para futuro)
  ingress {
    description     = "Kong proxy SSL from ALB"
    from_port       = 8443
    to_port         = 8443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # SSH para administración
  ingress {
    description = "SSH for management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restringir en producción
  }
  
  # Acceso temporal directo para pruebas iniciales
  ingress {
    description = "Direct Kong proxy access for testing"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Remover después de integrar con ALB
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-sg"
  })
}

# ==========================================
# SECURITY GROUP RULES - BACKEND ACCESS
# ==========================================

# Permitir que Kong acceda a servidores Django
resource "aws_security_group_rule" "django_from_kong" {
  security_group_id        = aws_security_group.app.id
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access Django servers"
}

# Permitir que Kong acceda a Notifications service
resource "aws_security_group_rule" "notifications_from_kong" {
  security_group_id        = aws_security_group.notifications_sg.id
  type                     = "ingress"
  from_port                = 3001
  to_port                  = 3001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access Notifications service"
}