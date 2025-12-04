# Pruebas de Carga - Servicio de Pedidos

## 📋 Descripción

Pruebas de carga usando **Locust** para evaluar el rendimiento del servicio de pedidos implementado con Lambda Function URL.

## 🎯 Endpoint Bajo Prueba

```
https://txsntfwdg3cmiliy7d2uo343by0gyzcp.lambda-url.us-east-1.on.aws
```

## 📦 Instalación

```bash
pip install locust
```

## 🚀 Uso

### Opción 1: Script Interactivo (Recomendado)

```bash
./run_load_test.sh
```

Menú de opciones:
1. **Interfaz Web** - Control manual de la prueba
2. **Prueba Rápida** - 10 usuarios, 2 min
3. **Prueba Media** - 50 usuarios, 5 min
4. **Prueba Intensiva** - 100 usuarios, 10 min
5. **Prueba Personalizada** - Define tus parámetros

### Opción 2: Comandos Directos

**Con interfaz web:**
```bash
locust -f locustfile.py --host=https://txsntfwdg3cmiliy7d2uo343by0gyzcp.lambda-url.us-east-1.on.aws
```
Luego abre: http://localhost:8089

**Sin interfaz (headless):**
```bash
locust -f locustfile.py \
    --host=https://txsntfwdg3cmiliy7d2uo343by0gyzcp.lambda-url.us-east-1.on.aws \
    --users 20 \
    --spawn-rate 5 \
    --run-time 3m \
    --headless \
    --html report.html
```

## 📊 Tareas Simuladas

El test simula usuarios que realizan las siguientes operaciones:

| Tarea | Peso | Descripción |
|-------|------|-------------|
| `crear_pedido_simple` | 10 | Crea pedido con 1-3 productos |
| `crear_pedido_grande` | 5 | Crea pedido con 5-8 productos |
| `listar_pedidos` | 3 | Lista todos los pedidos |
| `listar_pedidos_cliente` | 2 | Lista pedidos de un cliente específico |

## 🎲 Datos de Prueba

- **Clientes**: IDs aleatorios entre 1-100
- **Productos**: 10 productos predefinidos (Laptop, Monitor, Teclado, etc.)
- **Cantidades**: Aleatorias entre 1-10 unidades
- **Wait time**: 1-3 segundos entre requests

## 📈 Métricas Clave

### Éxito de la Prueba
- **Response time (median)**: < 500ms
- **Response time (95th percentile)**: < 1000ms
- **Failure rate**: < 1%
- **Requests per second**: Variable según usuarios

### Monitoreo Lambda
- **Cold starts**: Primera invocación puede tomar 1-2s
- **Warm executions**: ~200-400ms
- **Concurrency**: Lambda escala automáticamente
- **Throttling**: Monitorear límites de cuenta AWS

## 🔍 Interpretación de Resultados

### Respuestas Esperadas

**Creación de pedidos exitosa (201):**
```json
{
  "message": "Pedido creado exitosamente",
  "pedido": {
    "numero_pedido": "PED-000001",
    "cliente_id": 42,
    "total": 1500.00,
    "estado": "pendiente"
  }
}
```

**Lista de pedidos (200):**
```json
{
  "pedidos": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

### Errores Posibles

- **500**: Error en MongoDB o Lambda
- **502**: Bad Gateway (Lambda timeout o error no capturado)
- **504**: Gateway Timeout (Lambda excedió timeout)
- **429**: Throttling de Lambda (límite de concurrencia)

## 💡 Recomendaciones

### Para Pruebas Iniciales
```bash
# Empezar con carga baja
--users 10 --spawn-rate 2 --run-time 2m
```

### Para Evaluar Capacidad
```bash
# Incrementar gradualmente
--users 50 --spawn-rate 5 --run-time 5m
```

### Para Pruebas de Estrés
```bash
# Carga alta
--users 100 --spawn-rate 10 --run-time 10m
```

## 📁 Reportes Generados

Los reportes HTML incluyen:
- **Charts**: Tiempo de respuesta y RPS
- **Statistics**: Min, max, median, 95th percentile
- **Failures**: Listado de errores
- **Exceptions**: Stack traces si aplica

## 🐛 Troubleshooting

### Locust no instalado
```bash
pip install locust
```

### Error de conexión
Verifica que la Lambda Function URL sea accesible:
```bash
curl -X GET https://txsntfwdg3cmiliy7d2uo343by0gyzcp.lambda-url.us-east-1.on.aws/pedidos
```

### Muchos errores 500
- Verifica MongoDB esté corriendo
- Revisa CloudWatch Logs de Lambda
- Verifica Security Groups permitan conexión

### Errores 429 (Throttling)
- Lambda alcanzó límite de concurrencia
- Reduce número de usuarios o spawn rate
- Solicita aumento de límites a AWS

## 🔗 Referencias

- [Locust Documentation](https://docs.locust.io/)
- [AWS Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [Function URL Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html)
