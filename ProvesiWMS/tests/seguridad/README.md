# Pruebas de Seguridad - ProvesiWMS

## Objetivo

Validar que el sistema ProvesiWMS mantiene la seguridad de los datos y previene accesos no autorizados, específicamente:
- Ningún atacante puede modificar información de pedidos sin credenciales válidas (100% de protección)
- El sistema rechaza todas las formas de bypass de autenticación
- Los usuarios legítimos mantienen acceso normal después de intentos de ataque

## Estructura de Archivos

### Pruebas de Atacante
- `Anti_Modificacion_Pedidos_Atacante.postman_collection.json` - Simulación de atacante sin credenciales
- `Security_Tests_Atacante.postman_collection.json` - Suite completa de ataques de seguridad
- `Anti_Modificacion_API_Pedidos.postman_collection.json` - Ataques específicos a endpoints API

### Validación de Funcionalidad
- `Legitimate_User_Tests.postman_collection.json` - Verificación que usuarios legítimos pueden operar
- `Security_Validation_Corrected.postman_collection.json` - Validación general de medidas de seguridad

### Documentación
- `PRUEBAS_SEGURIDAD_README.md` - Guía detallada de ejecución y análisis

## Categorías de Pruebas

### 1. Acceso Sin Autenticación
- Intentos de acceder a endpoints sin token JWT
- Creación/modificación de pedidos sin credenciales
- Acceso a información sensible sin autorización

### 2. Tokens Inválidos
- JWT tokens falsos o malformados
- Tokens expirados
- Headers de autorización manipulados

### 3. Ataques de Inyección
- SQL Injection en formularios
- XSS (Cross-Site Scripting)
- Path traversal
- CSRF attacks

### 4. Bypass de Autenticación
- Basic Auth alternativo
- Parámetros de autenticación en URL
- Headers alternativos de autenticación

## Ejecución de Pruebas

### Requisitos
- Postman instalado
- Servidor ProvesiWMS funcionando
- URL base configurada en variables de Postman

### Configuración
1. Importar las colecciones en Postman
2. Configurar variable `base_url` con la URL del servidor
3. Ejecutar colecciones en el siguiente orden:

### Orden Recomendado
1. `Security_Tests_Atacante.postman_collection.json` - Pruebas principales de atacante
2. `Anti_Modificacion_Pedidos_Atacante.postman_collection.json` - Foco en pedidos
3. `Anti_Modificacion_API_Pedidos.postman_collection.json` - Validación API REST
4. `Legitimate_User_Tests.postman_collection.json` - Verificación de funcionalidad normal
5. `Security_Validation_Corrected.postman_collection.json` - Validación final

## Criterios de Éxito

### Resultado Exitoso (Sistema Seguro)
- TODAS las pruebas de atacante fallan (códigos 401, 403, 302)
- Ningún atacante puede crear/modificar/eliminar pedidos
- Usuarios legítimos pueden operar normalmente
- No se revelan datos sensibles en respuestas de error

### Resultado Problemático (Vulnerabilidad)
- CUALQUIER prueba de atacante tiene éxito (código 200, 201)
- Atacante puede acceder a información sin autenticación
- Tokens falsos son aceptados
- Inyecciones SQL/XSS tienen éxito

## Análisis de Resultados

### Indicadores Críticos
- Códigos de respuesta 200/201 en pruebas de atacante = VULNERABILIDAD CRÍTICA
- Acceso a endpoints sin token = FALLA DE AUTENTICACIÓN
- Ejecución de inyecciones = VULNERABILIDAD DE DATOS

### Acciones Correctivas
Si se detectan vulnerabilidades:
1. Implementar autenticación obligatoria en todos los endpoints
2. Validar y sanitizar todas las entradas de usuario
3. Configurar headers de seguridad apropiados
4. Implementar rate limiting
5. Re-ejecutar todas las pruebas hasta lograr 100% de protección

## Variables de Entorno

```json
{
  "base_url": "https://tu-servidor.com",
  "admin_username": "admin",
  "admin_password": "admin123"
}
```

## Reportes Automatizados

Cada colección genera reportes automáticos con:
- Resumen de vulnerabilidades encontradas
- Códigos de respuesta de cada prueba
- Recomendaciones de seguridad
- Estado general del sistema (SEGURO/VULNERABLE)

---

**Nota**: Estas pruebas deben ejecutarse regularmente y especialmente después de cada cambio en el código que afecte autenticación, autorización o endpoints de API.