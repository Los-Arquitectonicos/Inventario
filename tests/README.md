# Sistema de Gestión de Inventario - Suite de Pruebas

Este directorio contiene todos los archivos de prueba para el Sistema de Gestión de Inventario, organizados por tipo de prueba y propósito.

## Estructura del Directorio

### Pruebas API de Python
- **`api_functionality_test.py`** - Pruebas de funcionalidad principal de API con gestión de servidor Django
- **`complete_api_integration_test.py`** - Pruebas de integración comprensivas para todos los endpoints
- **`orders_api_test.py`** - Pruebas específicas para endpoints de API de pedidos/orders
- **`orders_functionality_test.py`** - Pruebas de lógica de negocio para funcionalidad de pedidos
- **`http_endpoints_test.py`** - Pruebas de validación de endpoints HTTP
- **`pedidos_endpoints_test.py`** - Pruebas específicas de endpoints de pedidos
- **`all_endpoints_validation_test.py`** - Suite completa de validación de endpoints

### Pruebas de Rendimiento JMeter
- **`aws_load_balancer_performance_test.jmx`** - Pruebas de rendimiento de Balanceador de Carga AWS (principal)
- **`pedidos_gui_functional_test.jmx`** - Pruebas funcionales compatibles con GUI para pedidos
- **`pedidos_performance_only_test.jmx`** - Pruebas puras de rendimiento sin assertions
- **`inventory_load_test.jmx`** - Pruebas de carga general del sistema de inventario
- **`inventory_readonly_test.jmx`** - Pruebas de rendimiento de operaciones de solo lectura

### Datos de Prueba y Utilidades
- **`setup_test_data.py`** - Crea datos de prueba base para el sistema
- **`setup_orders_test_data.py`** - Crea datos de prueba específicos para pedidos/orders
- **`test_results_summary.py`** - Genera resúmenes de ejecución de pruebas
- **`pedido_ids.csv`** - Archivo de datos de prueba con IDs de pedido para pruebas JMeter
- **`run_pedidos_jmeter_test.sh`** - Script shell para ejecutar pruebas JMeter de pedidos
- **`test_api.sh`** - Script shell para pruebas de API

## Guía de Uso

### Ejecutar Pruebas de Python
```bash
# Ejecutar pruebas comprensivas de API
python tests/api_functionality_test.py

# Ejecutar pruebas de integración completas
python tests/complete_api_integration_test.py

# Ejecutar pruebas específicas de pedidos
python tests/orders_api_test.py
```

### Ejecutar Pruebas JMeter
```bash
# Prueba de rendimiento de Balanceador de Carga AWS
jmeter -n -t tests/aws_load_balancer_performance_test.jmx -l results.jtl

# Prueba funcional compatible con GUI
jmeter -t tests/pedidos_gui_functional_test.jmx

# Prueba solo de rendimiento
jmeter -n -t tests/pedidos_performance_only_test.jmx -l performance.jtl
```

### Configurar Datos de Prueba
```bash
# Configurar datos de prueba básicos
python tests/setup_test_data.py

# Configurar datos específicos de pedidos
python tests/setup_orders_test_data.py
```

## Categorías de Pruebas

### 1. **Pruebas Funcionales**
- Verificar que los endpoints de API funcionen correctamente
- Probar implementación de lógica de negocio
- Validar integridad de datos

### 2. **Pruebas de Rendimiento**
- Medir tiempos de respuesta
- Probar sistema bajo carga
- Pruebas de Balanceador de Carga AWS

### 3. **Pruebas de Integración**
- Pruebas de flujo de trabajo de extremo a extremo
- Pruebas de interacción multi-componente
- Validación de integración de base de datos

## Configuración

### Pruebas de Balanceador de Carga AWS
Para pruebas AWS, configurar estas variables en `aws_load_balancer_performance_test.jmx`:
- `ALB_HOST`: Tu dominio de Balanceador de Carga AWS
- `ALB_PORT`: Puerto (80 para HTTP, 443 para HTTPS)

### Pruebas Locales
La mayoría de las pruebas están configuradas para ejecutarse contra:
- `http://127.0.0.1:8001` (servidor de prueba principal)
- `http://127.0.0.1:8002` (servidor de prueba alternativo)

## Resultados de Pruebas

Los resultados y logs de pruebas se limpian automáticamente. Usar las herramientas de resumen para generar reportes:
```bash
python tests/test_results_summary.py
```

## Mantenimiento

Esta suite de pruebas ha sido limpiada y organizada para:
- Remover archivos de prueba duplicados
- Usar nombres de archivo descriptivos
- Eliminar documentación redundante
- Organizar por tipo de prueba y propósito
- Mantener solo archivos de prueba esenciales