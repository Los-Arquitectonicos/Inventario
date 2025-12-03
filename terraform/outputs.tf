# Outputs principales de la infraestructura

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "HTTPS URL to access the application"
  value       = "https://${aws_lb.main.dns_name}/inventario/"
}

output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate in ACM"
  value       = aws_acm_certificate.alb_cert.arn
}

output "app_server_1_public_ip" {
  description = "Public IP address of application server 1"
  value       = aws_instance.app_server[0].public_ip
}

output "app_server_2_public_ip" {
  description = "Public IP address of application server 2"
  value       = aws_instance.app_server[1].public_ip
}

output "app_server_1_private_ip" {
  description = "Private IP address of application server 1"
  value       = aws_instance.app_server[0].private_ip
}

output "app_server_2_private_ip" {
  description = "Private IP address of application server 2"
  value       = aws_instance.app_server[1].private_ip
}

output "database_private_ip" {
  description = "Private IP address of the PostgreSQL database"
  value       = aws_instance.database.private_ip
}

output "vpc_id" {
  description = "ID of the default VPC being used"
  value       = data.aws_vpc.default.id
}

output "ssh_app_server_1" {
  description = "SSH command for application server 1"
  value       = "ssh ubuntu@${aws_instance.app_server[0].public_ip}"
}

output "notifications_public_ip" {
  description = "Public IP of Notifications Service"
  value       = aws_instance.notifications.public_ip
}

output "mongodb_private_ip" {
  description = "Private IP of MongoDB"
  value       = aws_instance.mongodb.private_ip
}

output "notifications_url" {
  description = "Notifications Service URL (via Kong Gateway)"
  value       = "https://${aws_lb.main.dns_name}/notifications"
}

output "ssh_app_server_2" {
  description = "SSH command for application server 2"
  value       = "ssh ubuntu@${aws_instance.app_server[1].public_ip}"
}

output "database_connection_string" {
  description = "PostgreSQL connection details"
  value       = "postgresql://inventario_user:${var.db_password}@${aws_instance.database.private_ip}:5432/inventario_db"
  sensitive   = true
}

# ===================================
# KONG API GATEWAY OUTPUTS
# ===================================

output "kong_gateway_public_ip" {
  description = "Public IP of Kong Gateway"
  value       = aws_instance.kong_gateway.public_ip
}

output "kong_gateway_private_ip" {
  description = "Private IP of Kong Gateway"
  value       = aws_instance.kong_gateway.private_ip
}

output "kong_admin_ssh" {
  description = "SSH command to access Kong Gateway for administration"
  value       = "ssh ubuntu@${aws_instance.kong_gateway.public_ip}"
}

output "kong_direct_url" {
  description = "Direct Kong Gateway URL (for testing)"
  value       = "http://${aws_instance.kong_gateway.public_ip}:8000"
}

output "api_gateway_url" {
  description = "Main API Gateway URL (via ALB)"
  value       = "https://${aws_lb.main.dns_name}"
}
