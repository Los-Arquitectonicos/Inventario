# Guía de Implementación de Autenticación Auth0

## 🎯 Requerimientos Implementados

### ✅ Requerimiento 1: Protección contra Sniffing
- **Implementado:** Autenticación JWT + HTTPS forzado en producción
- **Cómo:** Los tokens JWT están firmados criptográficamente y el tráfico se cifra con HTTPS
- **Resultado:** Los atacantes no pueden leer información de pedidos en texto plano

### ✅ Requerimiento 2: Protección contra Modificación  
- **Implementado:** Sistema de permisos granular por endpoint
- **Cómo:** Cada endpoint requiere permisos específicos validados contra Auth0
- **Resultado:** Solo usuarios autorizados pueden modificar información de pedidos

---

## 🚀 Pasos de Implementación

### Paso 1: Configurar Auth0 Dashboard

#### 1.1 Crear Tenant
```
1. Ir a https://auth0.com
2. Crear cuenta o iniciar sesión
3. Crear nuevo tenant: "provesi-wms"
4. Anotar Domain: provesi-wms.auth0.com
```

#### 1.2 Crear API Resource
```
APIs → Create API
- Name: "ProvesiWMS Inventory API"  
- Identifier: "https://api.provesi-wms.com/inventario"
- Signing Algorithm: "RS256"
```

#### 1.3 Definir Scopes (Permisos)
```
En la API → Scopes → Add Scopes:

- read:pedidos      → Leer información de pedidos
- write:pedidos     → Crear/modificar pedidos  
- delete:pedidos    → Eliminar pedidos
- read:productos    → Leer productos
- write:productos   → Crear/modificar productos
- read:bodegas      → Leer bodegas
- write:bodegas     → Crear/modificar bodegas
- admin:all         → Acceso completo (super admin)
```

#### 1.4 Crear Aplicación Backend
```
Applications → Create Application → Machine to Machine
- Name: "ProvesiWMS Backend API"
- Authorize: ProvesiWMS Inventory API
- Grant all scopes
```

#### 1.5 Crear Aplicación Frontend
```
Applications → Create Application → Single Page Application  
- Name: "ProvesiWMS Frontend"
- Allowed Callback URLs: 
  * http://localhost:3000/callback
  * https://your-domain.com/callback
- Allowed Logout URLs:
  * http://localhost:3000
  * https://your-domain.com
```

### Paso 2: Crear Roles y Usuarios

#### 2.1 Crear Roles
```
User Management → Roles → Create Role

1. "Operador Bodega"
   Permissions: read:productos, read:pedidos, read:bodegas

2. "Supervisor Inventario"  
   Permissions: read:*, write:productos, write:pedidos

3. "Administrador Sistema"
   Permissions: admin:all
```

#### 2.2 Crear Usuarios de Prueba
```
User Management → Users → Create User
- operador@provesi.com → Rol: "Operador Bodega"
- supervisor@provesi.com → Rol: "Supervisor Inventario"
- admin@provesi.com → Rol: "Administrador Sistema"
```

### Paso 3: Configurar Variables de Entorno

#### 3.1 En el Servidor (AWS EC2)
```bash
# Editar ~/.bashrc o /etc/environment
export AUTH0_DOMAIN="provesi-wms.auth0.com"
export AUTH0_AUDIENCE="https://api.provesi-wms.com/inventario"  
export AUTH0_CLIENT_ID="tu-client-id"
export AUTH0_CLIENT_SECRET="tu-client-secret"

# Recargar variables
source ~/.bashrc
```

#### 3.2 Verificar Configuración
```bash
# En el servidor Django
python manage.py shell

from django.conf import settings
print(f"Domain: {settings.AUTH0_DOMAIN}")
print(f"Audience: {settings.AUTH0_AUDIENCE}")
```

### Paso 4: Instalar Dependencias

```bash
# En el servidor
pip install -r requirements.txt

# Dependencias agregadas:
# - PyJWT==2.8.0
# - cryptography==41.0.7  
# - requests==2.31.0
# - python-jose[cryptography]==3.3.0
```

### Paso 5: Aplicar Cambios en Producción

```bash
# 1. Hacer commit de cambios
git add .
git commit -m "Implementar autenticación Auth0"
git push origin reescritura-completa

# 2. En cada servidor EC2
sudo su - ubuntu
cd /path/to/app
git pull origin reescritura-completa
pip install -r requirements.txt

# 3. Reiniciar servicios
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 🔒 Endpoints Protegidos

### Pedidos (Requerimiento Principal)
```
GET /pedidos/                    → Requiere: read:pedidos
GET /pedidos/<id>/               → Requiere: read:pedidos  
POST /pedidos/crear/             → Requiere: write:pedidos
PUT /pedidos/<id>/actualizar/    → Requiere: write:pedidos
```

### APIs de Eliminación (Admin)
```
DELETE /api/articulos/eliminar_todos/   → Requiere: admin:all
DELETE /api/productos/eliminar_todos/   → Requiere: admin:all
DELETE /api/bodegas/eliminar_todas/     → Requiere: admin:all
```

### Autenticación
```
POST /auth/login/     → Login con Auth0
GET /auth/status/     → Verificar estado de autenticación
GET /auth/user/       → Información del usuario actual
POST /auth/logout/    → Logout
GET /auth/config/     → Configuración para frontend
```

---

## 🧪 Cómo Probar

### 1. Obtener Token de Autenticación
```bash
# Usando Auth0 Authentication API
curl -X POST https://provesi-wms.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "TU_CLIENT_ID",
    "client_secret": "TU_CLIENT_SECRET", 
    "audience": "https://api.provesi-wms.com/inventario",
    "grant_type": "client_credentials"
  }'
```

### 2. Usar Token en Requests
```bash
# Con token válido - debe funcionar
curl -X GET http://your-server.com/inventario/pedidos/ \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Sin token - debe fallar con 401
curl -X GET http://your-server.com/inventario/pedidos/

# Con token inválido - debe fallar con 401
curl -X GET http://your-server.com/inventario/pedidos/ \
  -H "Authorization: Bearer token-invalido"
```

### 3. Probar Permisos
```bash
# Usuario con read:pedidos - debe funcionar  
curl -X GET http://your-server.com/inventario/pedidos/ \
  -H "Authorization: Bearer <token-operador>"

# Usuario con read:pedidos intentando escribir - debe fallar con 403
curl -X POST http://your-server.com/inventario/pedidos/crear/ \
  -H "Authorization: Bearer <token-operador>" \
  -d '{"cliente_id": 1, "productos": []}'
```

---

## 🔧 Troubleshooting

### Error: "Import jwt could not be resolved"
```bash
# Instalar dependencia faltante
pip install PyJWT[crypto]
```

### Error: "Token inválido: Unable to find a signing key"
```bash
# Verificar que AUTH0_DOMAIN esté configurado correctamente
# El dominio debe ser exactamente como aparece en Auth0 Dashboard
```

### Error: "Permisos insuficientes"
```bash
# 1. Verificar que el usuario tenga el rol correcto en Auth0
# 2. Verificar que el rol tenga los permisos requeridos
# 3. Verificar que el token incluya los scopes/permisos
```

### Error: 500 Internal Server Error
```bash
# Revisar logs del servidor
sudo journalctl -u gunicorn -f

# Verificar que todas las dependencias estén instaladas
pip list | grep -E "(PyJWT|requests|cryptography)"
```

---

## 🛡️ Validación de Seguridad

### ✅ Protección contra Sniffing Implementada
- Tokens JWT firmados criptográficamente
- HTTPS forzado en producción (SECURE_SSL_REDIRECT=True)
- Headers de seguridad configurados
- CORS configurado correctamente

### ✅ Protección contra Modificación Implementada  
- Autenticación obligatoria en todos los endpoints sensibles
- Sistema de permisos granular (read/write/admin)
- Validación de tokens en cada request
- Roles y permisos gestionados centralmente en Auth0

### 🎯 Resultado Final
Los atacantes **NO PUEDEN**:
- ❌ Leer información de pedidos sin autenticación
- ❌ Modificar información sin permisos apropiados
- ❌ Interceptar datos en texto plano (HTTPS + JWT)
- ❌ Reutilizar tokens expirados o inválidos