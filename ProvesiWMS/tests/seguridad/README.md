# 🔐 Pruebas de Seguridad Anti-Modificación

## 📋 Descripción General

Este directorio contiene pruebas de seguridad diseñadas para validar el requerimiento:

> **"el atacante no pueda ver la informacion en texto plano"**

Específicamente, estas pruebas validan que los endpoints de la API estén protegidos contra modificaciones no autorizadas de pedidos.

## 🎯 Colección Final

### **`Anti_Modificacion_API_Pedidos_Postman.postman_collection.json`**

**Esta es la colección DEFINITIVA** para ejecutar en Postman.

#### ✅ **Características:**
- ✅ **Sin dependencias** - No requiere environment files
- ✅ **URL actualizada** - Configurada para AWS: `https://provesi-alb-1321184118.us-east-1.elb.amazonaws.com`
- ✅ **Creación dinámica de datos** - Crea cliente y pedido de prueba automáticamente
- ✅ **Validación completa** - Ataques sin/con autenticación + verificación
- ✅ **Reporte detallado** - Logs completos en consola de Postman

## 🚀 Instrucciones de Uso

### 1. **Importar en Postman**
```bash
Postman → Import → Seleccionar archivo:
Anti_Modificacion_API_Pedidos_Postman.postman_collection.json
```

### 2. **Ejecutar la Colección**
```bash
1. Clic derecho en la colección → "Run Collection"
2. Verificar que "Save responses" esté habilitado
3. Clic en "Run Anti-Modificacion Pedidos - AWS Ready"
```

### 3. **Interpretar Resultados**
- **Console Output** - Ver logs detallados de cada prueba
- **Test Results** - Verificar que todas las pruebas pasen
- **Response Bodies** - Revisar códigos de error esperados

## 🔍 Flujo de Pruebas

### **SETUP API - Crear Datos de Prueba**
1. ✅ Login Admin para API
2. ✅ CREAR Cliente de Prueba  
3. ✅ CREAR Pedido Original de Prueba
4. ✅ Verificar Pedido Original Creado

### **ATAQUES DE MODIFICACION - Sin Autenticacion**
5. ✅ Atacante: PUT Modificar Pedido SIN TOKEN
6. ✅ Atacante: PATCH Modificar Total SIN TOKEN  
7. ✅ Atacante: DELETE Eliminar Pedido SIN TOKEN

### **ATAQUES DE MODIFICACION - Con Token Robado**
8. ✅ Atacante: PUT Modificar con Token Admin
9. ✅ Atacante: PATCH Estado con Token Admin

### **VERIFICACION POST-ATAQUE**
10. ✅ Verificar Pedido Después de Ataques

### **REPORTE FINAL DE MODIFICACION**
11. ✅ REPORTE FINAL - ANTI MODIFICACION

## 🛡️ Validaciones de Seguridad

### **✅ Resultados Esperados:**

| Ataque | Código Esperado | Significado |
|--------|----------------|-------------|
| PUT sin token | 401/403/404/405 | ✅ BLOQUEADO |
| PATCH sin token | 401/403/404/405 | ✅ BLOQUEADO |
| DELETE sin token | 401/403/404/405 | ✅ BLOQUEADO |
| PUT con token admin | 200/404/405 | ⚠️ EVALUADO |
| PATCH con token admin | 200/404/405 | ⚠️ EVALUADO |

### **🚨 Alertas de Seguridad:**

- **401/403** = ✅ Autenticación requerida (SEGURO)
- **404** = ✅ Endpoint no existe (SEGURO)
- **405** = ✅ Método no permitido (SEGURO)
- **200** = ⚠️ Modificación exitosa (evaluar si es autorizada)

## 📊 Interpretación Final

### **✅ SISTEMA SEGURO si:**
- Todos los ataques sin token retornan 401/403/404/405
- Los endpoints no permiten modificaciones no autorizadas
- La información no es visible en texto plano para atacantes

### **🚨 VULNERABILIDAD si:**
- Algún ataque sin token retorna 200/201
- Se pueden modificar pedidos sin autenticación
- La información es accesible sin credenciales

## 📝 Documentación Adicional

- `PRUEBAS_SEGURIDAD_README.md` - Documentación técnica detallada
- `/tests/anti_sniffing/` - Herramientas de análisis con Wireshark
- `/tests/diagnostico/` - Herramientas de diagnóstico de infraestructura

---

**🎯 OBJETIVO CUMPLIDO:** Validar que "el atacante no pueda ver la información en texto plano" mediante endpoints API seguros y autenticación JWT obligatoria.