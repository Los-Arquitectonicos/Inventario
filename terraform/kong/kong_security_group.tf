# ==========================================
# KONG API GATEWAY - SECURITY GROUP
# ==========================================
# ProvesiWMS Service Discovery
# ==========================================

# Security Group para Kong Gateway
resource "aws_security_group" "kong" {
  name        = "${var.project_prefix}-kong-sg"
  description = "Security group for Kong API Gateway"
  vpc_id      = data.aws_vpc.default.id

  # Proxy HTTP desde ALB (puerto principal)
  ingress {
    description     = "Kong proxy from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Status/Health check desde ALB
  ingress {
    description     = "Kong status from ALB"
    from_port       = 8100
    to_port         = 8100
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # SSH para administración
  ingress {
    description = "SSH for management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restringir en producción
  }

  # Permitir todo el tráfico saliente
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-sg"
  })
}

# Regla: Permitir que Kong acceda a los servidores Django
resource "aws_security_group_rule" "django_from_kong" {
  security_group_id        = aws_security_group.app.id
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access Django servers"
}

# Regla: Permitir que Kong acceda a la base de datos (para futuras integraciones)
resource "aws_security_group_rule" "db_from_kong" {
  security_group_id        = aws_security_group.db.id
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.kong.id
  description              = "Allow Kong to access database (for plugins)"
}
