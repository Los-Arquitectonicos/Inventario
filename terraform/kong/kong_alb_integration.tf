# ==========================================
# KONG API GATEWAY - ALB INTEGRATION
# ==========================================

# Target Group para Kong
resource "aws_lb_target_group" "kong" {
  name     = "${var.project_prefix}-kong-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id
  
  health_check {
    enabled             = true
    path                = "/status"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
    port                = "8000"
    protocol            = "HTTP"
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
# ALB LISTENER RULES - ROUTING TO KONG
# ==========================================

# Regla principal: Todo el tráfico va a Kong (prioridad más baja)
resource "aws_lb_listener_rule" "kong_default" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100  # Prioridad baja para que sea catch-all
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong.arn
  }
  
  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# Regla específica para API endpoints (prioridad alta)
resource "aws_lb_listener_rule" "kong_api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.kong.arn
  }
  
  condition {
    path_pattern {
      values = [
        "/api/*",
        "/inventario/*",
        "/notifications/*",
        "/admin/*",
        "/status"
      ]
    }
  }
}

# ==========================================
# COMMENT OUT OLD DJANGO DIRECT ROUTING
# ==========================================
# 
# NOTA: Comentar o eliminar las siguientes reglas del main.tf:
# - aws_lb_target_group.app
# - aws_lb_target_group_attachment.app_*  
# - aws_lb_listener_rule.django_*
#
# Todo el tráfico ahora pasa por Kong que enruta a Django