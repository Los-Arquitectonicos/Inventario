# 🚀 Scripts de Postman para Crear 50 Productos Distintos

Este directorio contiene dos enfoques para crear 50 productos distintos en el sistema ProvesiWMS usando Postman.

## 📁 Archivos Disponibles

### 1. **`postman_50_productos.json`** - Colección con Generación Dinámica
- **Enfoque**: Un solo request que genera productos aleatorios en cada ejecución
- **Uso**: Ejecutar 50 veces para crear 50 productos únicos
- **Ventaja**: Cada ejecución genera productos completamente diferentes

### 2. **`postman_50_productos_preconfigured.json`** - Colección Pre-configurada
- **Enfoque**: 50 requests individuales con productos específicos ya definidos
- **Uso**: Ejecutar la colección completa una sola vez
- **Ventaja**: Productos consistentes y reproducibles

### 3. **`generar_postman_50_productos.py`** - Generador Python
- **Enfoque**: Script que crea automáticamente la colección pre-configurada
- **Uso**: Ejecutar para regenerar la colección con nuevos productos
- **Ventaja**: Personalizable y extensible

## 🛠️ Instrucciones de Uso

### Opción A: Colección con Generación Dinámica

1. **Importar Colección**
   ```
   - Abre Postman
   - Click en "Import"
   - Selecciona "postman_50_productos.json"
   ```

2. **Configurar Runner**
   ```
   - Click en la colección importada
   - Selecciona "Run collection"
   - Configura:
     * Iterations: 50
     * Delay: 100ms (opcional)
   ```

3. **Ejecutar**
   ```
   - Click "Run ProvesiWMS - Crear 50 Productos"
   - Observa cómo se crean 50 productos únicos
   ```

### Opción B: Colección Pre-configurada

1. **Importar Colección**
   ```
   - Abre Postman
   - Click en "Import"  
   - Selecciona "postman_50_productos_preconfigured.json"
   ```

2. **Ejecutar Colección Completa**
   ```
   - Click en la colección importada
   - Selecciona "Run collection"
   - Click "Run ProvesiWMS - 50 Productos Distintos"
   ```

3. **Ver Resultados**
   ```
   - Se ejecutarán automáticamente 50 requests
   - Cada uno crea un producto específico
   ```

### Opción C: Regenerar Colección

1. **Ejecutar Generador**
   ```bash
   cd /ruta/al/proyecto
   python generar_postman_50_productos.py
   ```

2. **Importar Nueva Colección**
   ```
   - Se genera "postman_50_productos_preconfigured.json"
   - Importar en Postman como en Opción B
   ```

## 📊 Productos Incluidos

La colección incluye una amplia variedad de productos tecnológicos:

### Categorías
- 📱 **Smartphones** (iPhone, Galaxy, Pixel, etc.)
- 💻 **Laptops** (MacBook, ThinkPad, Gaming, etc.)  
- 📟 **Tablets** (iPad, Galaxy Tab, Surface, etc.)
- ⌚ **Smartwatches** (Apple Watch, Galaxy Watch, etc.)
- 🎧 **Auriculares** (AirPods, Bose, Sony, etc.)
- 🖥️ **Monitores** (Gaming, 4K, UltraWide, etc.)
- ⌨️ **Teclados** (Mecánicos, Gaming, Wireless, etc.)
- 🖱️ **Mouses** (Gaming, Ergonómicos, Precision, etc.)

### Marcas
```
Apple, Samsung, Sony, LG, Huawei, Xiaomi, OnePlus, Google,
Motorola, Nokia, HP, Dell, Lenovo, Asus, Acer, MSI, 
Logitech, Corsair, Razer, Bose, JBL, Canon, Nikon, y más...
```

## ⚙️ Configuración

### Variables de Entorno
```json
{
  "base_url": "http://127.0.0.1:8000"
}
```

### Headers Requeridos
```
Content-Type: application/json
Accept: application/json
```

## 🧪 Testing Automatizado

Cada request incluye tests automáticos que verifican:

```javascript
// Verificación de status exitoso
pm.test('Status code is 200', function () {
    pm.response.to.have.status(200);
});

// Verificación de estructura de respuesta
pm.test('Response has success field', function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
});

// Verificación de creación de producto
pm.test('Product was created successfully', function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.producto.id).to.be.above(0);
});
```

## 📈 Datos Generados

### Rangos de Precios (USD)
- **Smartphones**: $200 - $1,500
- **Laptops**: $500 - $3,000
- **Tablets**: $150 - $1,200
- **Smartwatches**: $100 - $800
- **Auriculares**: $50 - $500
- **Monitores**: $200 - $1,500
- **Teclados**: $30 - $300
- **Mouses**: $20 - $150

### Stock Inicial
- **Rango**: 5 - 100 unidades por producto
- **Distribución**: Aleatoria realista

### Especificaciones Técnicas
- **Peso**: Realista según categoría
- **Dimensiones**: Proporcionales al tipo de producto
- **Colores**: 22+ opciones variadas
- **Tallas**: Específicas por categoría

## 🚨 Prerrequisitos

1. **Django Server Activo**
   ```bash
   python manage.py runserver
   ```

2. **Base de Datos Configurada**
   ```bash
   python manage.py migrate
   ```

3. **Postman Instalado**
   - Desktop app o extensión web

## 🎯 Resultados Esperados

Después de ejecutar cualquiera de las opciones:

- ✅ **50 productos únicos** creados en la base de datos
- ✅ **Variedad de categorías** representadas
- ✅ **Datos realistas** en precios y especificaciones  
- ✅ **Stock inicial** para comenzar operaciones
- ✅ **Tests automáticos** confirmando creación exitosa

## 🔄 Personalización

Para modificar los productos generados, edita el archivo `generar_postman_50_productos.py`:

- **Agregar marcas**: Modifica el array `marcas`
- **Nuevas categorías**: Extiende el array `categorias`  
- **Rangos de precios**: Ajusta `precio_range` por categoría
- **Colores**: Personaliza el array `colores`
- **Cantidad**: Cambia el range en el bucle principal

¡Disfruta creando tu inventario completo con productos diversos y realistas! 🛒✨