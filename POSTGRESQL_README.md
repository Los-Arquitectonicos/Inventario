# 🐘 Configuración de PostgreSQL para el Sistema de Inventario

## ✅ Configuración Actual

El sistema ya está **configurado para PostgreSQL** en `inventario/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME', 'provesi_db'),
        'USER': os.getenv('DB_USER', 'provesi_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'provesi'),
        'HOST': os.getenv('DB_HOST', '172.31.18.62'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

## 🚀 Configuración Rápida

### 1. **Dependencias Instaladas**
```bash
✅ psycopg2-binary>=2.9.10  # Para conectar con PostgreSQL
✅ python-dotenv>=1.1.1     # Para variables de entorno
```

### 2. **Variables de Entorno**
Crea un archivo `.env` basado en `.env.example`:

```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita las credenciales según tu servidor PostgreSQL
nano .env
```

### 3. **Configuraciones de Ejemplo**

#### **Desarrollo Local:**
```env
DB_NAME=inventario_dev
DB_USER=postgres
DB_PASSWORD=password123
DB_HOST=localhost
DB_PORT=5432
```

#### **Producción (Actual):**
```env
DB_NAME=provesi_db
DB_USER=provesi_user
DB_PASSWORD=provesi
DB_HOST=172.31.18.62
DB_PORT=5432
```

#### **Docker Compose:**
```env
DB_NAME=inventario
DB_USER=inventario_user
DB_PASSWORD=secure_password_123
DB_HOST=postgres
DB_PORT=5432
```

## 🔧 Comandos de Migración

### **Aplicar Migraciones (Crear Tablas)**
```bash
python manage.py migrate
```

### **Crear Datos de Prueba**
```bash
python manage.py shell < tests/create_orders_test_data.py
```

### **Verificar Conexión**
```bash
python manage.py check --database default
```

## 🏪 Estructura de Tablas Creadas

Al ejecutar las migraciones se crean las siguientes tablas:

### **Tablas del Sistema de Inventario:**
- `inventario_categoria` - Categorías de productos
- `inventario_proveedor` - Proveedores
- `inventario_producto` - Catálogo de productos
- `inventario_bodega` - Bodegas/almacenes
- `inventario_zonabodega` - Zonas dentro de bodegas
- `inventario_articulo` - Artículos físicos individuales
- `inventario_movimientoarticulo` - Movimientos de inventario

### **Tablas del Sistema de Pedidos:**
- `inventario_pedido` - Pedidos/órdenes principales
- `inventario_detallepedido` - Líneas de productos en pedidos

### **Tablas de Django (automáticas):**
- `auth_user` - Usuarios del sistema
- `django_migrations` - Control de migraciones
- Otras tablas estándar de Django

## 🔍 Solución de Problemas

### **Error de Conexión**
```
psycopg2.OperationalError: connection to server failed
```

**Soluciones:**
1. ✅ Verificar que PostgreSQL esté corriendo
2. ✅ Verificar credenciales en `.env`
3. ✅ Verificar conectividad de red (ping al host)
4. ✅ Verificar firewall/puertos

### **Error de Autenticación**
```
psycopg2.OperationalError: FATAL: password authentication failed
```

**Soluciones:**
1. ✅ Verificar usuario y contraseña
2. ✅ Verificar permisos en PostgreSQL
3. ✅ Recrear usuario si es necesario

### **Base de Datos No Existe**
```
psycopg2.OperationalError: database "inventario" does not exist
```

**Crear base de datos:**
```sql
-- Conectar como superusuario y ejecutar:
CREATE DATABASE provesi_db;
CREATE USER provesi_user WITH PASSWORD 'provesi';
GRANT ALL PRIVILEGES ON DATABASE provesi_db TO provesi_user;
```

## 🎯 Estado Actual

✅ **PostgreSQL configurado**  
✅ **psycopg2 instalado**  
✅ **Variables de entorno configuradas**  
✅ **Migraciones preparadas**  
✅ **Sistema de pedidos implementado**

### **Para conectar con tu servidor PostgreSQL:**
1. Actualiza el archivo `.env` con tus credenciales
2. Ejecuta `python manage.py migrate`
3. Crea datos de prueba con el script proporcionado
4. ¡Listo para usar! 🚀

## 📞 Soporte

Si necesitas ayuda adicional:
- ✅ Verifica los logs de PostgreSQL
- ✅ Prueba conexión con `psql` directamente
- ✅ Revisa la configuración de red/firewall
- ✅ Contacta al administrador de base de datos