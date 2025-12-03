variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "mongodb_instance_type" {
  description = "EC2 instance type for MongoDB"
  type        = string
  default     = "t3.small"
}

variable "mongodb_volume_size" {
  description = "Size of MongoDB EBS volume in GB"
  type        = number
  default     = 20
}

variable "provesi_api_url" {
  description = "URL del API de ProvesiWMS para validaciones"
  type        = string
  default     = "http://your-provesi-alb-url.amazonaws.com"
}

variable "key_name" {
  description = "SSH key name for EC2"
  type        = string
  default     = "your-key-name"
}

variable "vpc_id" {
  description = "VPC ID donde desplegar recursos"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID para instancia MongoDB"
  type        = string
}
