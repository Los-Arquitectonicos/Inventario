# Outputs principales de la infraestructura

# ===================================
# KONG API GATEWAY - PUNTO DE ENTRADA ÚNICO
# ===================================

output "kong_public_ip" {
  description = "⭐ PUBLIC IP of Kong Gateway - USE THIS TO ACCESS THE APP"
  value       = aws_instance.kong_gateway.public_ip
}

output "kong_https_url" {
  description = "⭐ HTTPS URL to access the application via Kong"
  value       = "https://${aws_instance.kong_gateway.public_ip}"
}

output "kong_http_url" {
  description = "HTTP URL to access the application via Kong"
  value       = "http://${aws_instance.kong_gateway.public_ip}:8000"
}

output "kong_health_url" {
  description = "Kong health check endpoint"
  value       = "http://${aws_instance.kong_gateway.public_ip}:8100/status"
}

output "kong_ssh" {
  description = "SSH command to access Kong Gateway"
  value       = "ssh ubuntu@${aws_instance.kong_gateway.public_ip}"
}

# ===================================
# ALB (INTERNO - usado por Kong)
# ===================================

output "alb_dns_name" {
  description = "DNS name of the ALB (internal, used by Kong)"
  value       = aws_lb.main.dns_name
}

output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate in ACM"
  value       = aws_acm_certificate.alb_cert.arn
}

# ===================================
# DJANGO SERVERS (INTERNO)
# ===================================

output "app_server_public_ips" {
  description = "Public IPs of Django servers (for SSH only)"
  value       = aws_instance.app_server[*].public_ip
}

output "app_server_private_ips" {
  description = "Private IPs of Django servers"
  value       = aws_instance.app_server[*].private_ip
}

output "ssh_app_server_1" {
  description = "SSH command for application server 1"
  value       = "ssh ubuntu@${aws_instance.app_server[0].public_ip}"
}

output "ssh_app_server_2" {
  description = "SSH command for application server 2"
  value       = length(aws_instance.app_server) > 1 ? "ssh ubuntu@${aws_instance.app_server[1].public_ip}" : "N/A"
}

# ===================================
# DATABASE (INTERNO)
# ===================================

output "database_private_ip" {
  description = "Private IP address of the PostgreSQL database"
  value       = aws_instance.database.private_ip
}

output "database_connection_string" {
  description = "PostgreSQL connection details"
  value       = "postgresql://inventario_user:${var.db_password}@${aws_instance.database.private_ip}:5432/inventario_db"
  sensitive   = true
}

# ===================================
# VPC INFO
# ===================================

output "vpc_id" {
  description = "ID of the default VPC being used"
  value       = data.aws_vpc.default.id
}

# ===================================
# RESUMEN DE ACCESO
# ===================================

output "access_summary" {
  description = "Summary of how to access the application"
  value       = <<-EOT
  
  ==========================================
  🌐 ACCESO A LA APLICACIÓN
  ==========================================
  
  PUNTO DE ENTRADA ÚNICO (Kong):
    HTTPS: https://${aws_instance.kong_gateway.public_ip}
    HTTP:  http://${aws_instance.kong_gateway.public_ip}:8000
  
  RUTAS DISPONIBLES:
    /inventario/     - Aplicación principal
    /api/            - API REST
    /admin/          - Panel de administración
    /notifications/  - Microservicio de notificaciones
    /health          - Health check de Kong
  
  HEALTH CHECK:
    http://${aws_instance.kong_gateway.public_ip}:8100/status
  
  ==========================================
  EOT
}

# ===================================
# NOTIFICATIONS MICROSERVICE
# ===================================

output "notifications_server_ip" {
  description = "Private IP of Notifications microservice"
  value       = aws_instance.notifications.private_ip
}

output "notifications_server_public_ip" {
  description = "Public IP of Notifications microservice (for SSH)"
  value       = aws_instance.notifications.public_ip
}

output "notifications_api_url" {
  description = "URL to access Notifications API via Kong"
  value       = "https://${aws_instance.kong_gateway.public_ip}/notifications"
}

output "ssh_notifications" {
  description = "SSH command for Notifications server"
  value       = "ssh ubuntu@${aws_instance.notifications.public_ip}"
}

# ===================================
# MONGODB
# ===================================

output "mongodb_private_ip" {
  description = "Private IP of MongoDB server"
  value       = aws_instance.mongodb.private_ip
}

output "mongodb_public_ip" {
  description = "Public IP of MongoDB server (for SSH)"
  value       = aws_instance.mongodb.public_ip
}

output "ssh_mongodb" {
  description = "SSH command for MongoDB server"
  value       = "ssh ubuntu@${aws_instance.mongodb.public_ip}"
}

output "notifications_users" {
  description = "Default users for Notifications microservice"
  value       = <<-EOT
  
  ==========================================
  👤 USUARIOS DE NOTIFICACIONES
  ==========================================
  
  Los siguientes usuarios se crean automáticamente:
  
  | Usuario     | Contraseña     | Rol                       |
  |-------------|----------------|---------------------------|
  | admin       | admin123       | admin                     |
  | operario1   | operario123    | operario_bodega           |
  | empacador1  | empacador123   | empacador                 |
  | calidad1    | calidad123     | operario_control_calidad  |
  
  ==========================================
  EOT
}
