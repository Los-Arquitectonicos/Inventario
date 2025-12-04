# Pruebas de Seguridad - Microservicio de Notificaciones

Suite de pruebas de seguridad en Postman para verificar la autenticación, autorización y protección contra vulnerabilidades comunes en el microservicio de notificaciones.

## 📁 Archivos

- `Pruebas_Seguridad_Notificaciones.postman_collection.json` - Colección de Postman con todas las pruebas
- `Notificaciones_Security_Environment.postman_environment.json` - Entorno con variables configuradas

## 🎯 Categorías de Pruebas

### 1. Pruebas Sin Autenticación
- ❌ Listar notificaciones sin token (debe fallar con 401)
- ❌ Listar usuarios sin token (debe fallar con 401)
- ❌ Enviar notificación sin token (debe fallar con 401)

### 2. Pruebas Con Token Inválido
- ❌ Acceso con token malformado
- ❌ Acceso con formato de token incorrecto
- ❌ Acceso con token vacío

### 3. Setup - Obtener Tokens Válidos
- ✅ Login Admin
- ✅ Login Operario1
- ✅ Login Empacador

### 4. Pruebas de Autorización por Rol
- ❌ Operario intenta listar todos los usuarios (solo admin puede)
- ✅ Admin lista todos los usuarios
- ❌ Operario intenta ver detalles de otro usuario
- ✅ Admin ve detalles de cualquier usuario

### 5. Pruebas de Aislamiento de Datos
- ✅ Operario1 ve solo sus notificaciones
- ✅ Empacador ve solo sus notificaciones
- ❌ Empacador NO puede marcar como leída notificación de Operario1

### 6. Pruebas de Inyección y XSS
- ❌ SQL Injection en username
- ✅ Admin envía notificación con XSS (debe sanitizar)
- ✅ Verificar que XSS fue escapado

### 7. Pruebas de Rate Limiting (Opcional)
- Test múltiples intentos de login

## 🚀 Cómo usar

### 1. Importar en Postman

1. Abre Postman
2. Click en "Import"
3. Selecciona los dos archivos JSON:
   - `Pruebas_Seguridad_Notificaciones.postman_collection.json`
   - `Notificaciones_Security_Environment.postman_environment.json`

### 2. Configurar el entorno

1. Selecciona el entorno "Notificaciones Security Tests" en Postman
2. Verifica que `BASE_URL` apunta a: `https://3.238.225.18:8443`
3. Las demás variables se llenarán automáticamente al ejecutar las pruebas

### 3. Ejecutar las pruebas

#### Opción A: Ejecutar toda la colección

1. Click derecho en la colección "Pruebas de Seguridad - Microservicio Notificaciones"
2. Selecciona "Run collection"
3. Click en "Run Pruebas de Seguridad..."

#### Opción B: Ejecutar por carpetas

1. Ejecuta primero la carpeta "3. Setup - Obtener Tokens Válidos"
2. Luego ejecuta las demás carpetas en orden

#### Opción C: Ejecutar manualmente

1. Ejecuta cada request individualmente
2. Verifica los tests automáticos en la pestaña "Test Results"

### 4. Ejecutar desde línea de comando (Newman)

```bash
# Instalar Newman
npm install -g newman

# Ejecutar colección
newman run tests/seguridad/Pruebas_Seguridad_Notificaciones.postman_collection.json \
  -e tests/seguridad/Notificaciones_Security_Environment.postman_environment.json \
  --insecure

# Generar reporte HTML
newman run tests/seguridad/Pruebas_Seguridad_Notificaciones.postman_collection.json \
  -e tests/seguridad/Notificaciones_Security_Environment.postman_environment.json \
  --insecure \
  -r htmlextra \
  --reporter-htmlextra-export tests/seguridad/reporte_seguridad.html
```

## ✅ Criterios de Éxito

Todas las pruebas deben pasar:

- ✅ Los endpoints protegidos rechazan acceso sin token (401)
- ✅ Los endpoints rechazan tokens inválidos o malformados (401/403)
- ✅ Los usuarios solo pueden acceder a sus propias notificaciones
- ✅ Solo admin puede listar todos los usuarios
- ✅ Solo admin puede ver detalles de otros usuarios
- ✅ Los intentos de SQL Injection son rechazados
- ✅ El contenido XSS es escapado o sanitizado
- ✅ Los usuarios no pueden modificar datos de otros usuarios

## 🔒 Vulnerabilidades Probadas

- **Broken Authentication**: Acceso sin credenciales válidas
- **Broken Authorization**: Acceso a recursos sin permisos adecuados
- **Injection**: SQL/NoSQL injection en campos de entrada
- **XSS**: Cross-Site Scripting en mensajes
- **Insecure Direct Object References**: Acceso a notificaciones de otros usuarios
- **Missing Function Level Access Control**: Operaciones restringidas por rol

## 📊 Resultados Esperados

```
┌─────────────────────────┬─────────────────────┬────────────────────┐
│                         │            executed │             failed │
├─────────────────────────┼─────────────────────┼────────────────────┤
│              iterations │                   1 │                  0 │
├─────────────────────────┼─────────────────────┼────────────────────┤
│                requests │                  20 │                  0 │
├─────────────────────────┼─────────────────────┼────────────────────┤
│            test-scripts │                  40 │                  0 │
├─────────────────────────┼─────────────────────┼────────────────────┤
│      prerequest-scripts │                  20 │                  0 │
├─────────────────────────┼─────────────────────┼────────────────────┤
│              assertions │                  60 │                  0 │
└─────────────────────────┴─────────────────────┴────────────────────┘
```

## 🛠️ Solución de Problemas

### Error de certificado SSL

Si obtienes errores de certificado SSL:
- En Postman: Desactiva "SSL certificate verification" en Settings
- En Newman: Usa la flag `--insecure`

### BASE_URL incorrecta

Actualiza la variable `BASE_URL` en el entorno con la IP/DNS correcta de Kong.

### Tokens expirados

Si los tokens expiran durante las pruebas, vuelve a ejecutar la carpeta "3. Setup - Obtener Tokens Válidos".

## 📝 Notas

- Todas las pruebas se ejecutan contra Kong API Gateway (puerto 8443)
- Los tests verifican tanto el status code como el contenido de las respuestas
- Las variables de entorno se actualizan automáticamente con tokens y IDs
- Los tokens JWT tienen una duración de 24 horas por defecto
