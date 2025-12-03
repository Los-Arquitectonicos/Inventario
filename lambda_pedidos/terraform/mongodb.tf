# ==========================================
# EC2 INSTANCE FOR MONGODB
# ==========================================

resource "aws_security_group" "mongodb" {
  name        = "pedidos-mongodb-sg"
  description = "Security group for MongoDB instance"
  vpc_id      = var.vpc_id

  # MongoDB port from Lambda security group
  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
    description     = "MongoDB from Lambda"
  }

  # SSH access (opcional, para mantenimiento)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "pedidos-mongodb-sg"
  }
}

# User data para instalar y configurar MongoDB
data "template_file" "mongodb_user_data" {
  template = <<-EOF
    #!/bin/bash
    set -e
    
    echo "=== Instalando MongoDB en Ubuntu 24.04 ==="
    
    # Actualizar sistema
    apt-get update
    apt-get install -y gnupg curl
    
    # Importar clave pública de MongoDB
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
      gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    # Agregar repositorio de MongoDB
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
      tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    # Instalar MongoDB
    apt-get update
    apt-get install -y mongodb-org
    
    # Configurar MongoDB para aceptar conexiones remotas
    sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
    
    # Crear base de datos y usuario
    systemctl enable mongod
    systemctl start mongod
    
    # Esperar que MongoDB inicie
    sleep 10
    
    # Crear índices iniciales
    mongosh pedidos_db --eval '
      db.orders.createIndex({"numero_pedido": 1}, {unique: true});
      db.orders.createIndex({"cliente_id": 1});
      db.orders.createIndex({"estado": 1});
      db.orders.createIndex({"fecha_creacion": -1});
    '
    
    echo "=== MongoDB instalado y configurado ==="
  EOF
}

resource "aws_instance" "mongodb" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.mongodb_instance_type
  key_name               = var.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.mongodb.id]
  
  user_data = data.template_file.mongodb_user_data.rendered

  root_block_device {
    volume_size = var.mongodb_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "pedidos-mongodb"
  }
}

# AMI de Ubuntu 24.04
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd*/ubuntu-*-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
