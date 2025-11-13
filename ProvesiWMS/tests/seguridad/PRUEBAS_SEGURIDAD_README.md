# Pruebas de Seguridad - ProvesiWMS

## Objetivo

Validar que **un atacante NO puede modificar la información de pedidos** cuando el sistema está en línea, cumpliendo con el requisito de seguridad del 100%.

## Archivos de Prueba

### 1. `Security_Tests_Atacante.postman_collection.json`
**Propósito:** Simular a un atacante sin credenciales válidas intentando acceder y modificar datos del sistema.

**Categorías de Ataque:**
- **Test 1: Acceso Sin Autenticación** - Intentar crear/modificar pedidos sin token
- **Test 2: Tokens Falsos/Inválidos** - Usar tokens JWT falsos o malformados
- **Test 3: Bypass de Autenticación** - Intentar evadir autenticación con métodos alternativos
- **Test 4: Ataques de Inyección** - SQL injection, XSS, path traversal
- **Test 5: Acceso a Endpoints Administrativos** - Intentar acceder a funciones admin
- **Test 6: Ataques de Fuerza Bruta** - Múltiples intentos de login
- **Test 7: Resumen de Seguridad** - Validación de headers y reporte final

### 2. `Legitimate_User_Tests.postman_collection.json`
**Propósito:** Validar que usuarios autenticados pueden usar el sistema normalmente después de las pruebas de seguridad.

**Funcionalidades:**
- **Autenticación Legítima** - Login válido con credenciales correctas
- **Gestión de Productos** - Operaciones permitidas con JWT válido
- **Gestión de Pedidos** - Crear y modificar pedidos con autorización
- **Validación Final** - Verificar que el sistema funciona normalmente

## Configuración en Postman

### Paso 1: Importar Colecciones
1. Abrir **Postman**
2. Hacer clic en **"Import"**
3. Seleccionar los archivos:
   - `Security_Tests_Atacante.postman_collection.json`
   - `Legitimate_User_Tests.postman_collection.json`

### Paso 2: Configurar Variables
Las colecciones están preconfiguradas con:
```
base_url: https://provesi-alb-2003818714.us-east-1.elb.amazonaws.com
```

**Para cambiar la URL del servidor:**
1. Ir a la colección → Variables
2. Modificar `base_url` con tu URL del Load Balancer

## Ejecución de Pruebas

### Opción A: Ejecución Manual (Recomendada)

1. **Ejecutar primero: Pruebas de Atacante**
   ```
   Colección: "Security Tests - Atacante Sin Credenciales"
   ```
   - Ejecutar carpeta por carpeta en orden
   - Verificar que TODAS las pruebas pasen (ataques bloqueados)
   - Revisar el reporte en la consola de cada test

2. **Ejecutar después: Pruebas Legítimas**
   ```
   Colección: "Funcionalidad Legítima - Usuario Autenticado"
   ```
   - Verificar que usuarios autorizados pueden usar el sistema
   - Validar que el sistema funciona normalmente

### Opción B: Ejecución con Collection Runner

1. **Atacante (debe fallar todo):**
   - Colección → Run Collection
   - Ejecutar todas las pruebas
   - **Resultado esperado: 100% de ataques bloqueados**

2. **Usuarios Legítimos (debe funcionar):**
   - Colección → Run Collection
   - **Resultado esperado: 100% de operaciones exitosas**

## Interpretación de Resultados

### Resultado Exitoso (Seguridad OK)

```
PRUEBAS DE ATACANTE:
- Test 1-6: TODAS las pruebas PASAN (ataques bloqueados)
- Códigos HTTP: 401, 403 (Unauthorized, Forbidden)
- Console logs: "X ataques bloqueados"

PRUEBAS LEGÍTIMAS:
- Todos los tests PASAN (funcionalidad normal)
- Códigos HTTP: 200, 201 (Success)
- Tokens JWT válidos funcionan correctamente
```

### Resultado Problemático (Falla de Seguridad)

```
PROBLEMA DE SEGURIDAD:
- Algún test de atacante FALLA (ataque exitoso)
- Códigos HTTP: 200, 201 cuando deberían ser 401/403
- El atacante logró crear/modificar datos
```

### Qué Verificar en Cada Test

**Tests de Atacante (deben fallar):**
- No debe poder crear pedidos sin token
- No debe poder modificar pedidos existentes
- No debe poder eliminar pedidos
- Tokens falsos/malformados deben ser rechazados
- Inyecciones SQL/XSS deben ser bloqueadas
- No debe acceder a funciones administrativas

**Tests Legítimos (deben funcionar):**
- Login con credenciales válidas funciona
- Tokens JWT válidos permiten operaciones
- Usuarios autorizados pueden gestionar pedidos
- Sistema mantiene funcionalidad después de ataques

## Escenarios de Prueba Específicos

### Escenario 1: "Atacante intenta modificar pedido existente"
```http
PUT /inventario/api/pedidos/1/
Authorization: [SIN TOKEN O TOKEN FALSO]
Body: {"estado": "completado", "total": 999999}

Resultado Esperado: 401 Unauthorized
```

### Escenario 2: "Atacante intenta crear pedido malicioso"
```http
POST /inventario/api/pedidos/
Authorization: Bearer token_falso_123
Body: {"cliente_id": "1'; DROP TABLE pedidos; --"}

Resultado Esperado: 401/403 + Inyección SQL bloqueada
```

### Escenario 3: "Usuario legítimo modifica pedido"
```http
PUT /inventario/api/pedidos/1/
Authorization: Bearer [TOKEN_VÁLIDO_JWT]
Body: {"estado": "en_proceso"}

Resultado Esperado: 200 OK
```

## Reporte de Resultados

Al final de las pruebas, verificar:

1. **Contador de ataques bloqueados** (variable `attack_attempts`)
2. **Console logs** con resumen de seguridad
3. **Headers de seguridad** presentes (HSTS, X-Frame-Options, etc.)
4. **Funcionalidad preservada** para usuarios autenticados

### Ejemplo de Reporte Exitoso:
```
REPORTE DE SEGURIDAD - 2025-11-13T10:30:00.000Z
Total de intentos de ataque: 15
Expectativa: 100% de ataques bloqueados
RESUMEN COMPLETO DE PRUEBAS:
Todas las pruebas de atacante fueron bloqueadas
La funcionalidad legítima funciona correctamente
🏆 Sistema seguro y funcional al 100%
```

## 🚀 Antes de Ejecutar

**Asegurar que el sistema esté ejecutándose:**
```bash
# Verificar que Django esté corriendo en ambos servidores
curl -k https://tu-alb-url/inventario/

# Debe responder con la página principal de Django
# Si responde 502 Bad Gateway, verificar que Django esté corriendo
```

## Troubleshooting

### Error 502 Bad Gateway
```bash
# En cada servidor EC2:
cd ~/Inventario/ProvesiWMS
nohup python3 manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
```

### Variables de entorno
Si es necesario actualizar la URL del Load Balancer:
1. Obtener URL actual: `terraform output alb_url`
2. Actualizar variable `base_url` en ambas colecciones

### Credenciales de prueba
```
Admin: admin / ProvesiAdmin2024!
Gerente: gerente / gerente123
```

---

**Objetivo Final:** Comprobar que el sistema cumple el requisito **"el atacante no puede modificar la información de los pedidos dado que el sistema está en línea"** al 100%.