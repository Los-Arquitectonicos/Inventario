# ============================================================
# NOTIFICATIONS MICROSERVICE INFRASTRUCTURE
# ============================================================
# This file creates:
# - MongoDB EC2 instance
# - Notifications (FastAPI) EC2 instance  
# - Security Groups for both
# - IAM Role for SES access
# ============================================================

# ============ SECURITY GROUPS ============

# Security Group for MongoDB
resource "aws_security_group" "mongodb" {
  name        = "${var.project_prefix}-mongodb-sg"
  description = "Security group for MongoDB server"
  vpc_id      = data.aws_vpc.default.id

  # MongoDB from Notifications service only
  ingress {
    description     = "MongoDB from Notifications"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.notifications.id]
  }

  # SSH for debugging
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
  description = "Security group for Notifications microservice"
  vpc_id      = data.aws_vpc.default.id

  # FastAPI from Kong only
  ingress {
    description     = "FastAPI from Kong"
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.kong.id]
  }

  # SSH for debugging
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


# ============ IAM ROLE FOR SES ============

# IAM Role for Notifications EC2 to send emails via SES
resource "aws_iam_role" "notifications_ses" {
  name = "${var.project_prefix}-notifications-ses-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_prefix}-notifications-ses-role"
  }
}

# IAM Policy for SES send email
resource "aws_iam_role_policy" "notifications_ses_policy" {
  name = "${var.project_prefix}-notifications-ses-policy"
  role = aws_iam_role.notifications_ses.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "notifications" {
  name = "${var.project_prefix}-notifications-profile"
  role = aws_iam_role.notifications_ses.name
}


# ============ MONGODB EC2 INSTANCE ============

resource "aws_instance" "mongodb" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.mongodb_instance_type
  vpc_security_group_ids      = [aws_security_group.mongodb.id]
  associate_public_ip_address = true
  
  # Use first available subnet
  subnet_id = element(tolist(data.aws_subnets.available.ids), 0)

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOT
#!/bin/bash
set -e
exec > >(tee /var/log/mongodb-install.log|logger -t mongodb -s 2>/dev/console) 2>&1

echo "=========================================="
echo "Starting MongoDB Installation"
echo "=========================================="

# Update system
apt-get update -y
apt-get upgrade -y

# Install prerequisites
apt-get install -y gnupg curl

# Import MongoDB GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository (Ubuntu 24.04 = noble, but using jammy for compatibility)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
   tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update and install MongoDB
apt-get update -y
apt-get install -y mongodb-org

# Configure MongoDB to listen on all interfaces
cat > /etc/mongod.conf << 'MONGOD_CONF'
# mongod.conf

# Where and how to store data.
storage:
  dbPath: /var/lib/mongodb

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

# network interfaces
net:
  port: 27017
  bindIp: 0.0.0.0

# process management
processManagement:
  timeZoneInfo: /usr/share/zoneinfo
MONGOD_CONF

# Start and enable MongoDB
systemctl daemon-reload
systemctl start mongod
systemctl enable mongod

# Wait for MongoDB to start
sleep 5

# Verify MongoDB is running
mongosh --eval "db.adminCommand('ping')" && echo "✅ MongoDB is running!" || echo "❌ MongoDB failed to start"

echo "=========================================="
echo "MongoDB Installation Complete"
echo "=========================================="
EOT

  tags = {
    Name = "${var.project_prefix}-mongodb"
  }
}


# ============ NOTIFICATIONS EC2 INSTANCE ============

resource "aws_instance" "notifications" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.notifications_instance_type
  vpc_security_group_ids      = [aws_security_group.notifications.id]
  iam_instance_profile        = aws_iam_instance_profile.notifications.name
  associate_public_ip_address = true
  
  # Use first available subnet
  subnet_id = element(tolist(data.aws_subnets.available.ids), 0)

  # Wait for MongoDB to be ready
  depends_on = [aws_instance.mongodb]

  user_data = <<-EOT
#!/bin/bash
set -e
exec > >(tee /var/log/notifications-install.log|logger -t notifications -s 2>/dev/console) 2>&1

echo "=========================================="
echo "Starting Notifications Service Installation"
echo "=========================================="

# Update system
apt-get update -y
apt-get upgrade -y

# Install Python and dependencies
apt-get install -y python3 python3-pip python3-venv git

# Create app directory
mkdir -p /opt/apps
cd /opt/apps

# Clone repository
git clone https://github.com/Los-Arquitectonicos/Inventario.git
cd Inventario
git checkout servicediscovery

# Create virtual environment
python3 -m venv /opt/apps/venv
source /opt/apps/venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r /opt/apps/Inventario/notifications/requirements.txt

# Set environment variables
cat >> /etc/environment << 'ENV_VARS'
MONGODB_HOST="${aws_instance.mongodb.private_ip}"
MONGODB_PORT="27017"
MONGODB_DATABASE="notifications_db"
JWT_SECRET_KEY="notifications-jwt-secret-${random_string.jwt_secret.result}"
AWS_REGION="${var.aws_region}"
SENDER_EMAIL="pedropablost@icloud.com"
DEFAULT_RECIPIENT="p.sanin@uniandes.edu.co"
PORT="8001"
ENV_VARS

# Export for current session
export MONGODB_HOST="${aws_instance.mongodb.private_ip}"
export MONGODB_PORT="27017"
export MONGODB_DATABASE="notifications_db"
export JWT_SECRET_KEY="notifications-jwt-secret-${random_string.jwt_secret.result}"
export AWS_REGION="${var.aws_region}"
export SENDER_EMAIL="pedropablost@icloud.com"
export DEFAULT_RECIPIENT="p.sanin@uniandes.edu.co"
export PORT="8001"

# Create startup script
cat > /opt/apps/start_notifications.sh << 'START_SCRIPT'
#!/bin/bash
cd /opt/apps/Inventario/notifications
source /opt/apps/venv/bin/activate
source /etc/environment
exec uvicorn main:app --host 0.0.0.0 --port 8001
START_SCRIPT

chmod +x /opt/apps/start_notifications.sh

# Create systemd service
cat > /etc/systemd/system/notifications.service << 'SYSTEMD_SERVICE'
[Unit]
Description=Notifications Microservice (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/apps/Inventario/notifications
EnvironmentFile=/etc/environment
ExecStart=/opt/apps/start_notifications.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SYSTEMD_SERVICE

# Wait for MongoDB to be accessible
echo "Waiting for MongoDB at ${aws_instance.mongodb.private_ip}:27017..."
for i in {1..30}; do
    if nc -z ${aws_instance.mongodb.private_ip} 27017 2>/dev/null; then
        echo "✅ MongoDB is accessible!"
        break
    fi
    echo "Attempt $i/30: MongoDB not ready yet..."
    sleep 5
done

# Install netcat for health checks
apt-get install -y netcat-openbsd

# Enable and start service
systemctl daemon-reload
systemctl enable notifications
systemctl start notifications

# Wait for service to start
sleep 5

# Check if service is running
systemctl status notifications --no-pager || echo "Service may still be starting..."

echo "=========================================="
echo "Notifications Service Installation Complete"
echo "=========================================="
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
