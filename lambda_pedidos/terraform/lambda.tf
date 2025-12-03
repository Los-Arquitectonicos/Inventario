# ==========================================
# IAM ROLE FOR LAMBDA
# ==========================================

resource "aws_iam_role" "lambda_role" {
  name = "pedidos-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Política para CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Política para VPC (para acceder a MongoDB en EC2)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# ==========================================
# LAMBDA LAYER (shared code)
# ==========================================

resource "aws_lambda_layer_version" "pedidos_layer" {
  filename            = "${path.module}/../layer.zip"
  layer_name          = "pedidos-shared-layer"
  compatible_runtimes = ["python3.11", "python3.12"]
  
  description = "Shared code for pedidos Lambda functions (models, db_client, etc)"
}

# ==========================================
# SECURITY GROUP FOR LAMBDA
# ==========================================

resource "aws_security_group" "lambda" {
  name        = "pedidos-lambda-sg"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "pedidos-lambda-sg"
  }
}

# ==========================================
# LAMBDA FUNCTIONS
# ==========================================

# Lambda: Crear Pedido
resource "aws_lambda_function" "crear_pedido" {
  filename      = "${path.module}/../functions/crear_pedido.zip"
  function_name = "pedidos-crear"
  role          = aws_iam_role.lambda_role.arn
  handler       = "crear_pedido.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  layers = [aws_lambda_layer_version.pedidos_layer.arn]

  environment {
    variables = {
      MONGODB_URI     = "mongodb://${aws_instance.mongodb.private_ip}:27017/pedidos_db"
      PROVESI_API_URL = var.provesi_api_url
    }
  }

  vpc_config {
    subnet_ids         = [var.subnet_id]
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# Lambda: Consultar Pedido
resource "aws_lambda_function" "consultar_pedido" {
  filename      = "${path.module}/../functions/consultar_pedido.zip"
  function_name = "pedidos-consultar"
  role          = aws_iam_role.lambda_role.arn
  handler       = "consultar_pedido.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  layers = [aws_lambda_layer_version.pedidos_layer.arn]

  environment {
    variables = {
      MONGODB_URI     = "mongodb://${aws_instance.mongodb.private_ip}:27017/pedidos_db"
      PROVESI_API_URL = var.provesi_api_url
    }
  }

  vpc_config {
    subnet_ids         = [var.subnet_id]
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# Lambda: Seguir Pedido
resource "aws_lambda_function" "seguir_pedido" {
  filename      = "${path.module}/../functions/seguir_pedido.zip"
  function_name = "pedidos-seguir"
  role          = aws_iam_role.lambda_role.arn
  handler       = "seguir_pedido.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  layers = [aws_lambda_layer_version.pedidos_layer.arn]

  environment {
    variables = {
      MONGODB_URI     = "mongodb://${aws_instance.mongodb.private_ip}:27017/pedidos_db"
      PROVESI_API_URL = var.provesi_api_url
    }
  }

  vpc_config {
    subnet_ids         = [var.subnet_id]
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# ==========================================
# CLOUDWATCH LOG GROUPS
# ==========================================

resource "aws_cloudwatch_log_group" "crear_pedido" {
  name              = "/aws/lambda/${aws_lambda_function.crear_pedido.function_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "consultar_pedido" {
  name              = "/aws/lambda/${aws_lambda_function.consultar_pedido.function_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "seguir_pedido" {
  name              = "/aws/lambda/${aws_lambda_function.seguir_pedido.function_name}"
  retention_in_days = 7
}
