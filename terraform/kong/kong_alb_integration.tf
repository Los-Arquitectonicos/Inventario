# ==========================================
# KONG API GATEWAY - ALB INTEGRATION
# ==========================================
# ProvesiWMS Service Discovery
# ==========================================

# Target Group para Kong Gateway
resource "aws_lb_target_group" "kong" {
  name     = "${var.project_prefix}-kong-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    enabled             = true
    path                = "/status"
    port                = "8100"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-kong-tg"
  })
}

# Registrar instancia Kong en Target Group
resource "aws_lb_target_group_attachment" "kong" {
  target_group_arn = aws_lb_target_group.kong.arn
  target_id        = aws_instance.kong_gateway.id
  port             = 8000
}

# ==========================================
# LISTENER RULES - Enrutamiento a través de Kong
# ==========================================

# Regla: Rutas de API van a Kong (máxima prioridad)
resource "aws_lb_listener_rule" "kong_api_routes" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/inventario/*"]
    }
  }
}

# Regla: Ruta de admin de Django va a Kong
resource "aws_lb_listener_rule" "kong_admin_routes" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong.arn
  }

  condition {
    path_pattern {
      values = ["/admin/*"]
    }
  }
}

# Regla: Health check de Kong
resource "aws_lb_listener_rule" "kong_health" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 5

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong.arn
  }

  condition {
    path_pattern {
      values = ["/kong-health"]
    }
  }
}

# ==========================================
# NOTA: El default action del listener HTTPS
# ya apunta a los servidores Django directamente.
# Las reglas de arriba redirigen tráfico específico
# a través de Kong para service discovery.
# 
# Para hacer que TODO el tráfico pase por Kong,
# modificar el default_action en main.tf para
# apuntar a aws_lb_target_group.kong.arn
# ==========================================
