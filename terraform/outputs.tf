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
  description = "Public IP of Kong Gateway instance (for SSH access)"
  value       = aws_instance.kong_gateway.public_ip
}

output "kong_gateway_private_ip" {
  description = "Private IP of Kong Gateway instance"
  value       = aws_instance.kong_gateway.private_ip
}

output "kong_admin_ssh" {
  description = "SSH command to access Kong Gateway for administration"
  value       = "ssh ubuntu@${aws_instance.kong_gateway.public_ip}"
}

output "kong_admin_tunnel" {
  description = "SSH tunnel command to access Kong Admin API"
  value       = "ssh -L 8001:localhost:8001 ubuntu@${aws_instance.kong_gateway.public_ip}"
}

output "kong_proxy_url" {
  description = "Kong proxy URL (via ALB)"
  value       = "https://${aws_lb.main.dns_name}/api/"
}

output "kong_health_check_url" {
  description = "Kong health check endpoint (direct)"
  value       = "http://${aws_instance.kong_gateway.public_ip}:8100/status"
}
