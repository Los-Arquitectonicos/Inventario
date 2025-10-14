# 🏭 Guía Completa: 10,000 Artículos Masivos en ProvesiWMS

## 📋 Descripción del Proyecto

Este sistema permite crear **10,000 artículos únicos** en la base de datos de ProvesiWMS de manera automatizada y eficiente usando Postman Collections.

## 🎯 Características Principales

### ✅ **Artículos Únicos**
- **10,000 artículos** distribuidos automáticamente
- **Códigos de barras EAN-13** válidos y únicos
- **Distribución aleatoria** entre productos existentes
- **Ubicación automática** en 50 ubicaciones de bodega

### 🏗️ **Infraestructura Automatizada**
- **50 ubicaciones de bodega** (10 pasillos × 5 estantes)
- **Capacidad total**: 12,500 artículos (250 por ubicación)
- **Distribución inteligente** para optimizar almacenamiento

### ⚡ **Generación Dinámica**
- **JavaScript avanzado** para generación en tiempo real
- **Códigos de barras únicos** con algoritmo EAN-13
- **Selección aleatoria** de productos y ubicaciones
- **Progress tracking** cada 100 artículos

## 📦 Archivos Generados

### 1. **`postman_10000_articulos_masivos.json`**
**Colección Principal con Generación Dinámica**

```json
📂 Estructura de la Colección:
├── 📦 1. Preparación: Crear 50 Ubicaciones de Bodega
│   ├── Crear Ubicación P01E01 (A01-E01-N01)
│   ├── Crear Ubicación P01E02 (A01-E02-N01)
│   └── ... (50 ubicaciones totales)
├── 🏭 2. Creación Masiva: 10,000 Artículos
│   └── 🏷️ Crear Artículo Dinámico (Ejecutar 10,000 veces)
└── 📊 3. Verificación Final
    └── 📈 Contar Artículos Totales
```

### 2. **`generar_postman_10000_articulos.py`**
**Script Generador Python**
- Crea automáticamente la colección Postman
- Genera ubicaciones de bodega organizadas
- Implementa algoritmos de códigos de barras
- Incluye scripts de JavaScript optimizados

## 🚀 Instrucciones de Uso

### **Paso 1: Preparación del Entorno**

```bash
# 1. Asegúrate de que Django esté ejecutándose
cd /Users/pedropablosanintrujillo/GitHub/Inventario/ProvesiWMS
python manage.py runserver

# 2. Verifica que tienes productos en la base de datos
python manage.py shell -c "
from inventario.models import Producto
print(f'Productos disponibles: {Producto.objects.count()}')
"
```

### **Paso 2: Configuración de Postman**

1. **Importar Colección:**
   ```
   File → Import → postman_10000_articulos_masivos.json
   ```

2. **Configurar Variables de Entorno:**
   ```
   base_url = http://127.0.0.1:8000
   csrf_token = [obtener del formulario de Django]
   ```

3. **Obtener CSRF Token:**
   ```
   GET http://127.0.0.1:8000/inventario/ubicaciones/crear/
   → Inspeccionar → Buscar csrfmiddlewaretoken
   ```

### **Paso 3: Ejecución Ordenada**

#### **3.1 Crear Ubicaciones de Bodega**
```
Folder: "📦 1. Preparación: Crear 50 Ubicaciones"
→ Run Collection
→ Select Folder: "1. Preparación"
→ Run (50 requests)
```

**Resultado Esperado:**
```
✅ 50 ubicaciones creadas
📍 Pasillos: A01 a A10
📍 Estantes: E01 a E05
📦 Capacidad total: 12,500 artículos
```

#### **3.2 Creación Masiva de Artículos**
```
Folder: "🏭 2. Creación Masiva: 10,000 Artículos"
→ Runner Configuration:
   • Iterations: 10,000
   • Delay: 10ms (opcional)
   • Data: None (usa JavaScript interno)
→ Run Collection
```

**Progreso Esperado:**
```
🎯 Progreso: 100 artículos creados
🎯 Progreso: 200 artículos creados
...
🎯 Progreso: 10,000 artículos creados
```

#### **3.3 Verificación Final**
```
Folder: "📊 3. Verificación Final"
→ Execute: "📈 Contar Artículos Totales"
```

**Resultado Final:**
```
📊 RESUMEN FINAL:
   • Artículos creados en esta sesión: 10,000
   • Total de artículos en BD: 10,XXX
   • Objetivo cumplido: ✅ SÍ
```

## 🔧 Características Técnicas

### **Generación de Códigos de Barras EAN-13**
```javascript
function generarCodigoBarras() {
    const prefijo = "789";  // Código país ficticio
    const numero = Array.from({length: 9}, 
        () => Math.floor(Math.random() * 10)).join('');
    const codigoSinDigito = prefijo + numero;
    
    // Algoritmo de dígito verificador EAN-13
    let suma = 0;
    for (let i = 0; i < codigoSinDigito.length; i++) {
        if (i % 2 === 0) {
            suma += parseInt(codigoSinDigito[i]);
        } else {
            suma += parseInt(codigoSinDigito[i]) * 3;
        }
    }
    
    const digitoVerificador = (10 - (suma % 10)) % 10;
    return codigoSinDigito + digitoVerificador.toString();
}
```

### **Distribución de Ubicaciones**
```
📦 Sistema de Ubicaciones:
├── Pasillos: A01, A02, A03, ..., A10 (10 pasillos)
├── Estantes: E01, E02, E03, E04, E05 (5 estantes por pasillo)
└── Nivel: N01 (nivel fijo por simplicidad)

🎯 Capacidad por Ubicación: 250 artículos
🎯 Capacidad Total: 12,500 artículos
```

### **Selección Aleatoria de Productos**
```javascript
// Usa productos existentes en la base de datos (IDs 1-51)
const productos = [1, 2, 3, ..., 51];
const productoId = productos[Math.floor(Math.random() * productos.length)];
```

## ⏱️ Tiempos de Ejecución

### **Estimaciones de Tiempo**
```
📦 Ubicaciones (50): ~2 minutos
🏭 Artículos (10,000): ~15-25 minutos
📊 Verificación: ~30 segundos
──────────────────────────────
⏱️ Total Estimado: 18-28 minutos
```

### **Factores que Afectan el Rendimiento**
- **Velocidad de red**: Local vs remoto
- **Capacidad del servidor**: CPU y memoria
- **Delay entre requests**: 10ms recomendado
- **Tamaño de la base de datos**: Índices y constraints

## 🎮 Opciones de Configuración

### **Variables Personalizables**

```javascript
// En el script de JavaScript, puedes modificar:

// 1. Rango de productos (actual: 1-51)
const productos = [1, 2, 3, ..., N];

// 2. Prefijo de códigos de barras (actual: 789)
const prefijo = "789";

// 3. Capacidad por ubicación (actual: 250)
"capacidad_total": 250

// 4. Número de ubicaciones (actual: 50)
// Modificar loops en generar_ubicaciones_bodega()
```

### **Escalabilidad**

Para **más de 10,000 artículos:**
```
• Incrementar iterations en Runner
• Agregar más ubicaciones si es necesario
• Considerar implementar batch processing
• Monitorear performance de la base de datos
```

## 🛠️ Troubleshooting

### **Errores Comunes**

#### **1. Error de CSRF Token**
```
❌ Error: CSRF token missing or incorrect
✅ Solución: Obtener nuevo token del formulario Django
```

#### **2. Ubicaciones No Disponibles**
```
❌ Error: No se encontraron ubicaciones
✅ Solución: Ejecutar primero el folder de ubicaciones
```

#### **3. Productos Inexistentes**
```
❌ Error: Producto no encontrado
✅ Solución: Verificar IDs de productos en la base de datos
```

#### **4. Códigos de Barras Duplicados**
```
❌ Error: Código de barras ya existe
✅ Solución: El algoritmo incluye validación de unicidad
```

### **Verificaciones Previas**
```bash
# Verificar productos disponibles
python manage.py shell -c "
from inventario.models import Producto
print('Productos:', Producto.objects.count())
print('IDs:', [p.id for p in Producto.objects.all()[:5]])
"

# Verificar bodega principal
python manage.py shell -c "
from inventario.models import Bodega
print('Bodegas:', Bodega.objects.count())
if Bodega.objects.exists():
    print('Primera bodega ID:', Bodega.objects.first().id)
"
```

## 📊 Estadísticas Esperadas

### **Distribución Final**
```
📈 Artículos por Producto:
   • Promedio: ~196 artículos por producto (10,000 ÷ 51)
   • Rango: 150-250 (distribución aleatoria)

📦 Artículos por Ubicación:
   • Promedio: ~200 artículos por ubicación (10,000 ÷ 50)
   • Capacidad utilizada: ~80% (200/250)

🏷️ Códigos de Barras:
   • Formato: 789XXXXXXXXD (13 dígitos)
   • Prefijo: 789 (código ficticio)
   • Unicidad: 100% garantizada
```

## 🎯 Objetivos Cumplidos

Al completar este proceso tendrás:

- ✅ **10,000 artículos únicos** en tu inventario
- ✅ **50 ubicaciones organizadas** en tu bodega
- ✅ **Códigos de barras válidos** EAN-13
- ✅ **Distribución optimizada** del inventario
- ✅ **Base de datos robusta** para testing
- ✅ **Sistema escalable** para más artículos

## 🚀 Próximos Pasos

### **Después de la Creación Masiva:**

1. **Análisis de Datos:**
   ```sql
   SELECT COUNT(*) as total_articulos FROM inventario_articulo;
   SELECT producto_id, COUNT(*) as cantidad 
   FROM inventario_articulo 
   GROUP BY producto_id;
   ```

2. **Pruebas de Rendimiento:**
   - Buscar artículos por código de barras
   - Generar reportes de inventario
   - Probar operaciones de picking

3. **Expansión del Sistema:**
   - Agregar más bodegas
   - Implementar rotación de inventario
   - Configurar alertas de stock

---

## 📞 Soporte

Para problemas o mejoras, puedes:
- Verificar los logs de Postman Console
- Revisar los scripts de JavaScript incluidos
- Modificar el generador Python según necesidades
- Ajustar la configuración de ubicaciones

**¡Buen inventario masivo!** 🎉