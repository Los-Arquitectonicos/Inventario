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
  default     = "InventarioSecure2024!"
  sensitive   = true
}

# ===================================
# VARIABLES DE SEGURIDAD Y AUTENTICACIÓN
# ===================================

variable "django_secret_key" {
  description = "Django SECRET_KEY for cryptographic signing (must be unique and secret)"
  type        = string
  default     = "django-insecure-CHANGE-THIS-IN-PRODUCTION-xyz789abc123def456ghi"
  sensitive   = true
  
  validation {
    condition     = length(var.django_secret_key) >= 50
    error_message = "Django SECRET_KEY must be at least 50 characters long for security."
  }
}

variable "environment" {
  description = "Deployment environment (production, staging, development)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "debug_mode" {
  description = "Enable Django DEBUG mode (should be false for production)"
  type        = bool
  default     = false
}

variable "allowed_hosts" {
  description = "List of allowed hosts for Django ALLOWED_HOSTS setting"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default     = []
}

# ===================================
# VARIABLES DE BASE DE DATOS
# ===================================

variable "database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "inventario_db"
}

variable "database_user" {
  description = "PostgreSQL database username"
  type        = string
  default     = "inventario_user"
}

variable "database_port" {
  description = "PostgreSQL database port"
  type        = number
  default     = 5432
}

# ===================================
# VARIABLES DE JWT CONFIGURACIÓN
# ===================================

variable "jwt_access_token_lifetime_hours" {
  description = "JWT access token lifetime in hours"
  type        = number
  default     = 1
  
  validation {
    condition     = var.jwt_access_token_lifetime_hours > 0 && var.jwt_access_token_lifetime_hours <= 24
    error_message = "JWT access token lifetime must be between 1 and 24 hours."
  }
}

variable "jwt_refresh_token_lifetime_days" {
  description = "JWT refresh token lifetime in days"
  type        = number
  default     = 7
  
  validation {
    condition     = var.jwt_refresh_token_lifetime_days > 0 && var.jwt_refresh_token_lifetime_days <= 30
    error_message = "JWT refresh token lifetime must be between 1 and 30 days."
  }
}

# ===================================
# VARIABLES DE CERTIFICADO SSL
# ===================================

variable "enable_https" {
  description = "Enable HTTPS listener on ALB (requires SSL certificate)"
  type        = bool
  default     = true
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for HTTPS (leave empty to skip HTTPS setup)"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Custom domain name for the application"
  type        = string
  default     = ""
}

# ===================================
# VARIABLES DE LOGGING Y MONITOREO
# ===================================

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logging for application instances"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

# ===================================
# VARIABLES DE CONFIGURACIÓN AVANZADA
# ===================================

variable "app_server_count" {
  description = "Number of application servers to deploy"
  type        = number
  default     = 2
  
  validation {
    condition     = var.app_server_count >= 1 && var.app_server_count <= 10
    error_message = "Application server count must be between 1 and 10."
  }
}

variable "gunicorn_workers" {
  description = "Number of Gunicorn worker processes per server"
  type        = number
  default     = 4
  
  validation {
    condition     = var.gunicorn_workers >= 1 && var.gunicorn_workers <= 16
    error_message = "Gunicorn workers must be between 1 and 16."
  }
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling for application servers"
  type        = bool
  default     = false
}

variable "min_servers" {
  description = "Minimum number of servers in auto scaling group"
  type        = number
  default     = 2
}

variable "max_servers" {
  description = "Maximum number of servers in auto scaling group"
  type        = number
  default     = 6
}

variable "desired_servers" {
  description = "Desired number of servers in auto scaling group"
  type        = number
  default     = 2
}

variable "backup_retention_days" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

# ===================================
# KONG API GATEWAY VARIABLES
# ===================================

variable "kong_instance_type" {
  description = "EC2 instance type for Kong Gateway"
  type        = string
  default     = "t3.small"
}

variable "kong_version" {
  description = "Kong Gateway version to install"
  type        = string
  default     = "3.5.0"
}

variable "kong_log_level" {
  description = "Kong logging level (debug, info, notice, warn, error, crit)"
  type        = string
  default     = "info"
  
  validation {
    condition     = contains(["debug", "info", "notice", "warn", "error", "crit"], var.kong_log_level)
    error_message = "Kong log level must be one of: debug, info, notice, warn, error, crit."
  }
}

variable "enable_kong_admin_api" {
  description = "Enable Kong Admin API on public interface (not recommended for production)"
  type        = bool
  default     = false
}

# ===================================
# VARIABLES ADICIONALES PARA TERRAFORM.TFVARS
# ===================================

variable "owner" {
  description = "Owner tag for AWS resources"
  type        = string
  default     = "devops"
}

variable "database_instance_type" {
  description = "Database instance type (alias for db_instance_type)"
  type        = string
  default     = "t3.small"
}

variable "database_password" {
  description = "Database password (alias for db_password)"
  type        = string
  default     = "InventarioSecure2024!"
  sensitive   = true
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "database_storage_gb" {
  description = "Database storage size in GB"
  type        = number
  default     = 100

  validation {
    condition     = var.database_storage_gb >= 20 && var.database_storage_gb <= 1000
    error_message = "Database storage must be between 20 and 1000 GB."
  }
}

variable "force_https" {
  description = "Force HTTPS redirects"
  type        = bool
  default     = true
}

variable "cors_allow_credentials" {
  description = "Allow credentials in CORS requests"
  type        = bool
  default     = false
}

variable "ssl_policy" {
  description = "SSL policy for ALB"
  type        = string
  default     = "ELBSecurityPolicy-TLS-1-2-2017-01"
}

variable "log_level" {
  description = "Application logging level"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}
