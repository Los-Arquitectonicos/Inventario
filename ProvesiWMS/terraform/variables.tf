# Archivo de configuración de variables con valores por defecto
# Puedes sobrescribir estos valores creando un archivo terraform.tfvars

variable "region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"
}

variable "project_prefix" {
  description = "Prefix for naming all AWS resources"
  type        = string
  default     = "provesi"
}

variable "instance_type" {
  description = "EC2 instance type for application servers"
  type        = string
  default     = "t2.small"
}

variable "db_instance_type" {
  description = "EC2 instance type for database server"
  type        = string
  default     = "t2.micro"
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  default     = "inventario2024"
  sensitive   = true
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH into instances (default: anywhere)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
