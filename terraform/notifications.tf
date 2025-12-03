# ============================================================
# NOTIFICATIONS MICROSERVICE INFRASTRUCTURE
# ============================================================

# Security Group for MongoDB
resource "aws_security_group" "mongodb" {
  name        = "${var.project_prefix}-mongodb-sg"
  description = "Security group for MongoDB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "MongoDB from Notifications"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.notifications.id]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-mongodb-sg"
  }
}

# Security Group for Notifications service
resource "aws_security_group" "notifications" {
  name        = "${var.project_prefix}-notifications-sg"
  description = "Security group for Notifications"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "FastAPI from Kong"
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.kong.id]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-notifications-sg"
  }
}

# MongoDB EC2 Instance
resource "aws_instance" "mongodb" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.mongodb_instance_type
  vpc_security_group_ids      = [aws_security_group.mongodb.id]
  associate_public_ip_address = true
  subnet_id                   = element(tolist(data.aws_subnets.available.ids), 0)

  user_data = <<-EOT
    #!/bin/bash
    
    # Install MongoDB
    sudo apt-get update -y
    sudo apt-get install -y gnupg curl
    
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    sudo apt-get update -y
    sudo apt-get install -y mongodb-org
    
    # Configure MongoDB to listen on all interfaces
    sudo sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/g' /etc/mongod.conf
    
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    echo "MongoDB started"
    EOT

  tags = {
    Name = "${var.project_prefix}-mongodb"
  }
}

# Notifications EC2 Instance
resource "aws_instance" "notifications" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.notifications_instance_type
  vpc_security_group_ids      = [aws_security_group.notifications.id]
  associate_public_ip_address = true
  subnet_id                   = element(tolist(data.aws_subnets.available.ids), 0)

  depends_on = [aws_instance.mongodb]

  user_data = <<-EOT
    #!/bin/bash
    
    # Variables
    MONGODB_HOST="${aws_instance.mongodb.private_ip}"
    
    # Set environment variables
    echo "MONGODB_HOST=${aws_instance.mongodb.private_ip}" | sudo tee -a /etc/environment
    echo "MONGODB_PORT=27017" | sudo tee -a /etc/environment
    echo "MONGODB_DATABASE=notifications_db" | sudo tee -a /etc/environment
    echo "JWT_SECRET_KEY=notifications-jwt-secret-2024" | sudo tee -a /etc/environment
    echo "EMAIL_ENABLED=false" | sudo tee -a /etc/environment
    echo "PORT=8001" | sudo tee -a /etc/environment
    
    # Install Python
    sudo apt-get update -y
    sudo apt-get install -y python3-pip python3-venv git
    
    # Clone repository
    cd /home/ubuntu
    git clone https://github.com/Los-Arquitectonicos/Inventario.git
    cd Inventario
    git checkout servicediscovery
    
    # Install dependencies
    sudo pip3 install --break-system-packages -r /home/ubuntu/Inventario/notifications/requirements.txt
    
    # Wait for MongoDB
    sleep 30
    
    # Start FastAPI
    cd /home/ubuntu/Inventario/notifications
    source /etc/environment
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /home/ubuntu/notifications.log 2>&1 &
    
    echo "Notifications service started"
    EOT

  tags = {
    Name = "${var.project_prefix}-notifications"
  }
}

# Random string for JWT secret
resource "random_string" "jwt_secret" {
  length  = 32
  special = false
}
