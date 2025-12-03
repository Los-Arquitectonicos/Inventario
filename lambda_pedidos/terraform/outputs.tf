output "api_gateway_url" {
  description = "URL del API Gateway"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/pedidos"
}

output "mongodb_private_ip" {
  description = "IP privada de la instancia MongoDB"
  value       = aws_instance.mongodb.private_ip
}

output "mongodb_public_ip" {
  description = "IP pública de la instancia MongoDB"
  value       = aws_instance.mongodb.public_ip
}

output "lambda_function_names" {
  description = "Nombres de las funciones Lambda creadas"
  value = {
    crear     = aws_lambda_function.crear_pedido.function_name
    consultar = aws_lambda_function.consultar_pedido.function_name
    seguir    = aws_lambda_function.seguir_pedido.function_name
  }
}

output "endpoints" {
  description = "Endpoints del API"
  value = {
    crear_pedido     = "POST ${aws_api_gateway_stage.prod.invoke_url}/pedidos"
    listar_pedidos   = "GET  ${aws_api_gateway_stage.prod.invoke_url}/pedidos"
    obtener_pedido   = "GET  ${aws_api_gateway_stage.prod.invoke_url}/pedidos/{numero_pedido}"
    seguir_pedido    = "PUT  ${aws_api_gateway_stage.prod.invoke_url}/pedidos/{numero_pedido}/seguimiento"
  }
}
