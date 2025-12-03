# ==========================================
# API GATEWAY REST API
# ==========================================

resource "aws_api_gateway_rest_api" "pedidos_api" {
  name        = "pedidos-api"
  description = "API Gateway para gestión de pedidos serverless"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# ==========================================
# RESOURCE: /pedidos
# ==========================================

resource "aws_api_gateway_resource" "pedidos" {
  rest_api_id = aws_api_gateway_rest_api.pedidos_api.id
  parent_id   = aws_api_gateway_rest_api.pedidos_api.root_resource_id
  path_part   = "pedidos"
}

# POST /pedidos (crear pedido)
resource "aws_api_gateway_method" "post_pedidos" {
  rest_api_id   = aws_api_gateway_rest_api.pedidos_api.id
  resource_id   = aws_api_gateway_resource.pedidos.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post_pedidos" {
  rest_api_id             = aws_api_gateway_rest_api.pedidos_api.id
  resource_id             = aws_api_gateway_resource.pedidos.id
  http_method             = aws_api_gateway_method.post_pedidos.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crear_pedido.invoke_arn
}

# GET /pedidos (listar pedidos)
resource "aws_api_gateway_method" "get_pedidos" {
  rest_api_id   = aws_api_gateway_rest_api.pedidos_api.id
  resource_id   = aws_api_gateway_resource.pedidos.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_pedidos" {
  rest_api_id             = aws_api_gateway_rest_api.pedidos_api.id
  resource_id             = aws_api_gateway_resource.pedidos.id
  http_method             = aws_api_gateway_method.get_pedidos.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.consultar_pedido.invoke_arn
}

# ==========================================
# RESOURCE: /pedidos/{numero_pedido}
# ==========================================

resource "aws_api_gateway_resource" "pedido_by_numero" {
  rest_api_id = aws_api_gateway_rest_api.pedidos_api.id
  parent_id   = aws_api_gateway_resource.pedidos.id
  path_part   = "{numero_pedido}"
}

# GET /pedidos/{numero_pedido}
resource "aws_api_gateway_method" "get_pedido" {
  rest_api_id   = aws_api_gateway_rest_api.pedidos_api.id
  resource_id   = aws_api_gateway_resource.pedido_by_numero.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_pedido" {
  rest_api_id             = aws_api_gateway_rest_api.pedidos_api.id
  resource_id             = aws_api_gateway_resource.pedido_by_numero.id
  http_method             = aws_api_gateway_method.get_pedido.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.consultar_pedido.invoke_arn
}

# ==========================================
# RESOURCE: /pedidos/{numero_pedido}/seguimiento
# ==========================================

resource "aws_api_gateway_resource" "seguimiento" {
  rest_api_id = aws_api_gateway_rest_api.pedidos_api.id
  parent_id   = aws_api_gateway_resource.pedido_by_numero.id
  path_part   = "seguimiento"
}

# PUT /pedidos/{numero_pedido}/seguimiento
resource "aws_api_gateway_method" "put_seguimiento" {
  rest_api_id   = aws_api_gateway_rest_api.pedidos_api.id
  resource_id   = aws_api_gateway_resource.seguimiento.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "put_seguimiento" {
  rest_api_id             = aws_api_gateway_rest_api.pedidos_api.id
  resource_id             = aws_api_gateway_resource.seguimiento.id
  http_method             = aws_api_gateway_method.put_seguimiento.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.seguir_pedido.invoke_arn
}

# ==========================================
# CORS CONFIGURATION
# ==========================================

module "cors_pedidos" {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.pedidos_api.id
  api_resource_id = aws_api_gateway_resource.pedidos.id
}

module "cors_pedido_by_numero" {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.pedidos_api.id
  api_resource_id = aws_api_gateway_resource.pedido_by_numero.id
}

module "cors_seguimiento" {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.pedidos_api.id
  api_resource_id = aws_api_gateway_resource.seguimiento.id
}

# ==========================================
# LAMBDA PERMISSIONS FOR API GATEWAY
# ==========================================

resource "aws_lambda_permission" "apigw_crear_pedido" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crear_pedido.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.pedidos_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_consultar_pedido" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.consultar_pedido.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.pedidos_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_seguir_pedido" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.seguir_pedido.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.pedidos_api.execution_arn}/*/*"
}

# ==========================================
# API DEPLOYMENT
# ==========================================

resource "aws_api_gateway_deployment" "pedidos" {
  rest_api_id = aws_api_gateway_rest_api.pedidos_api.id

  depends_on = [
    aws_api_gateway_integration.post_pedidos,
    aws_api_gateway_integration.get_pedidos,
    aws_api_gateway_integration.get_pedido,
    aws_api_gateway_integration.put_seguimiento
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.pedidos.id
  rest_api_id   = aws_api_gateway_rest_api.pedidos_api.id
  stage_name    = "prod"

  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/pedidos-api"
  retention_in_days = 7
}
