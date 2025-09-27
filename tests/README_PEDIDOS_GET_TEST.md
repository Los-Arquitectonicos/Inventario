# 📦 Test JMX de Pedidos GET - Sistema de Inventario

## 🎯 Descripción

Este archivo **`pedidos_get_test.jmx`** es un test JMeter especializado para probar únicamente las operaciones **GET del sistema de pedidos**, con enfoque especial en la función principal `obtener_ubicaciones_productos()`.

## ✨ Características del Test

### **Endpoints Probados:**
1. **`GET /pedidos/`** - Lista de todos los pedidos
2. **`GET /pedidos/{id}/`** - Pedido específico por ID
3. **`GET /pedidos/{id}/detalles/`** - Detalles completos del pedido
4. **`GET /pedidos/{id}/ubicaciones/`** - 🎯 **FUNCIÓN PRINCIPAL** - Ubicaciones de productos

### **Configuración del Test:**
- **👥 Usuarios Concurrentes:** 15 (configurable)
- **⏱️ Tiempo de Rampa:** 20 segundos
- **🔄 Iteraciones:** 3 por usuario
- **⏸️ Intervalo:** 800ms entre requests
- **⏱️ Timeouts:** 10s normal, 15s para ubicaciones

## 🚀 Cómo Ejecutar

### **Opción 1: Script Automático (Recomendado)**
```bash
# Ejecución básica
./tests/run_pedidos_test.sh

# Con parámetros personalizados
./tests/run_pedidos_test.sh 127.0.0.1 8000 20 30 5
#                           host     puerto threads ramp loops
```

### **Opción 2: JMeter Directo**
```bash
# Modo GUI (desarrollo)
jmeter -t tests/pedidos_get_test.jmx

# Modo línea de comandos (automatización)
jmeter -n -t tests/pedidos_get_test.jmx \
  -l pedidos_results.jtl \
  -e -o pedidos_report/

# Con parámetros customizados
jmeter -n -t tests/pedidos_get_test.jmx \
  -Jserver.host=127.0.0.1 \
  -Jserver.port=8000 \
  -Jthreads=25 \
  -Jramp.time=30 \
  -Jloops=5 \
  -l pedidos_stress.jtl \
  -e -o pedidos_stress_report/
```

## 📋 Preparación Previa

### **1. Datos de Prueba**
```bash
# Crear pedidos de ejemplo
python tests/create_orders_test_data.py

# Verificar que existen pedidos
curl http://localhost:8000/pedidos/
```

### **2. Servidor Django**
```bash
# Iniciar servidor
python manage.py runserver 8000

# Verificar endpoints
curl http://localhost:8000/pedidos/1/ubicaciones/
```

## 🎯 Función Principal Probada

### **`obtener_ubicaciones_productos(pedido_id)`**

**Endpoint:** `GET /pedidos/{id}/ubicaciones/`

**Propósito:** Retorna productos, cantidades y ubicaciones en bodega para un pedido dado.

**Respuesta Esperada:**
```json
{
  "success": true,
  "pedido_id": 1,
  "numero_pedido": "PED-B15DF370",
  "estado": "pendiente",
  "ubicaciones_productos": [
    {
      "producto_id": 1,
      "producto_nombre": "Laptop HP EliteBook",
      "producto_sku": "LAPTOP-001",
      "cantidad_pedida": 2,
      "cantidad_disponible": 2,
      "cantidad_faltante": 0,
      "precio_unitario": "1150.00",
      "subtotal": "2300.00",
      "ubicaciones": [
        {
          "bodega": "Bodega Principal",
          "bodega_id": 1,
          "codigo_bodega": "BOD-001",
          "cantidad_disponible": 2,
          "articulos": [
            {
              "id": 1,
              "codigo_interno": "LAPTOP-001-61C76D2C",
              "numero_serie": "LAPTOP-001-7A4985CE",
              "lote": "LOTE-202509-001",
              "zona": "Zona A",
              "ubicacion_completa": "Bodega Principal - Zona A"
            }
          ]
        }
      ],
      "completamente_disponible": true
    }
  ]
}
```

## 🔍 Validaciones del Test

### **Assertions HTTP:**
- ✅ **Status 200:** Todas las respuestas deben ser exitosas
- ✅ **Content-Type:** `application/json`
- ✅ **Response Time:** < 15 segundos para queries complejas

### **Assertions JSON:**
- ✅ **Lista Pedidos:** Campo `$.pedidos` debe existir
- ✅ **ID Pedido:** Campo `$.id` en pedidos específicos
- ✅ **Detalles:** Campo `$.detalles` en endpoint de detalles
- ✅ **Ubicaciones:** Campos `$.pedido_id` y `$.productos_ubicaciones`
- ✅ **Fecha Creación:** Campo `$.fecha_creacion` presente

### **Validaciones de Rendimiento:**
- 🎯 **Latencia Promedio:** < 500ms para endpoints simples
- 🎯 **Latencia Ubicaciones:** < 2000ms para queries complejas
- 🎯 **Throughput:** > 10 requests/segundo
- 🎯 **Tasa de Error:** 0%

## 📊 Interpretación de Resultados

### **Métricas Clave:**
```
📈 Requests Totales: Debe completar todos sin errores
⚡ Tiempo Respuesta Promedio: 
   • /pedidos/: 50-200ms
   • /pedidos/{id}/: 100-300ms
   • /pedidos/{id}/detalles/: 150-500ms
   • /pedidos/{id}/ubicaciones/: 500-2000ms (función compleja)

✅ Tasa de Éxito: 100%
🔄 Throughput: 10-50 req/sec según carga
```

### **Alertas de Performance:**
- 🔴 **> 3000ms** en `/ubicaciones/`: Revisar queries de base de datos
- 🔴 **Errores HTTP:** Verificar conectividad y datos
- 🟡 **> 1000ms promedio:** Considerar optimización de consultas

## 🛠️ Troubleshooting

### **Error: Connection Refused**
```bash
# Verificar servidor Django
python manage.py runserver 8000

# Verificar puerto disponible  
lsof -i :8000
```

### **Error: 404 Not Found**
```bash
# Verificar URLs en inventario/urls.py
python manage.py show_urls | grep pedidos
```

### **Error: No Data (Empty Response)**
```bash
# Crear datos de prueba
python tests/create_orders_test_data.py

# Verificar datos
python manage.py shell -c "from inventario.models import Pedido; print(Pedido.objects.count())"
```

### **Performance Issues**
```bash
# Verificar logs de Django
python manage.py runserver --verbosity=2

# Analizar queries SQL
# Añadir 'debug_toolbar' a INSTALLED_APPS para análisis detallado
```

## 📁 Archivos Relacionados

```
tests/
├── 📋 pedidos_get_test.jmx          # Este test JMX
├── 🚀 run_pedidos_test.sh           # Script de ejecución
├── 📊 create_orders_test_data.py    # Datos de prueba
├── 🧪 test_orders_functionality.py  # Tests Python
└── 📖 JMeter_README.md              # Documentación general
```

## 🎯 Casos de Uso del Test

### **Desarrollo:**
- ✅ Validar nuevas funcionalidades de pedidos
- ✅ Probar rendimiento después de cambios
- ✅ Verificar que la función principal funciona correctamente

### **Testing:**
- ✅ Pruebas de regresión automáticas
- ✅ Validación antes de despliegues
- ✅ Benchmarking de performance

### **Producción:**
- ✅ Monitoreo de salud del sistema
- ✅ Pruebas de carga regulares
- ✅ Validación después de mantenimientos

## ⚙️ Personalización del Test

### **Modificar Parámetros:**
```xml
<!-- En el archivo JMX, sección User Defined Variables -->
<stringProp name="THREADS">25</stringProp>        <!-- Usuarios -->
<stringProp name="RAMP_TIME">45</stringProp>      <!-- Rampa -->
<stringProp name="LOOPS">10</stringProp>          <!-- Loops -->
```

### **Añadir Nuevos Endpoints:**
```xml
<!-- Ejemplo: Añadir endpoint de estadísticas -->
<HTTPSamplerProxy testname="GET - Estadísticas Pedidos">
  <stringProp name="HTTPSampler.path">/pedidos/estadisticas/</stringProp>
  <!-- ... resto de configuración ... -->
</HTTPSamplerProxy>
```

## 🏆 Objetivos del Test

✅ **Validar la función principal:** `obtener_ubicaciones_productos()`  
✅ **Asegurar rendimiento:** Respuestas < 2000ms  
✅ **Verificar estabilidad:** 0% errores bajo carga normal  
✅ **Probar escalabilidad:** Múltiples usuarios concurrentes  
✅ **Garantizar disponibilidad:** APIs siempre responsivas  

**¡Este test asegura que el sistema de pedidos funcione perfectamente bajo carga!** 🚀