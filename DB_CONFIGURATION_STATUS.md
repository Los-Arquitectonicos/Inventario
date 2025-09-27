# 🐘 Configuración de Base de Datos PostgreSQL

## 📋 Variables de Entorno Configuradas

Crea o actualiza tu archivo `.env` con estas variables:

```bash
# PostgreSQL Configuración Principal
DB_NAME=provesi_db
DB_USER=provesi_user
DB_PASSWORD=provesi
DB_HOST=172.31.18.62
DB_PORT=5432

# Configuración de Fallback
USE_POSTGRES=true
FALLBACK_TO_SQLITE=true
DEBUG=True
```

## 🔧 Estados de Configuración

### **PostgreSQL Activo (Actual)**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'provesi_db',
        'USER': 'provesi_user',
        'PASSWORD': 'provesi',
        'HOST': '172.31.18.62',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

## 🌐 Estado de Conectividad

### **Server PostgreSQL:**
- **Host:** `172.31.18.62:5432`
- **Estado:** ❌ Timeout de conexión
- **Error:** `connection to server failed: timeout expired`
- **Timeout:** 10 segundos

### **Posibles Causas:**
1. **🔥 Firewall:** Puerto 5432 bloqueado
2. **🌐 Conectividad:** Red o VPN desconectada  
3. **⏸️ Servidor:** PostgreSQL detenido
4. **🔐 Configuración:** Credenciales incorrectas

## 🛠️ Soluciones Disponibles

### **Opción 1: Usar PostgreSQL Local**
```bash
# Instalar PostgreSQL localmente
brew install postgresql
brew services start postgresql

# Crear base de datos local
createdb provesi_db
createuser -s provesi_user
```

**Actualizar .env:**
```bash
DB_HOST=localhost
DB_PORT=5432
```

### **Opción 2: Usar Docker PostgreSQL**
```bash
# Ejecutar PostgreSQL en Docker
docker run --name postgres-inventario \
  -e POSTGRES_DB=provesi_db \
  -e POSTGRES_USER=provesi_user \
  -e POSTGRES_PASSWORD=provesi \
  -p 5432:5432 \
  -d postgres:15

# Actualizar .env
DB_HOST=localhost
```

### **Opción 3: Configuración Dual Inteligente**
Agrega esta función a `settings.py` para fallback automático:

```python
def get_database_config():
    postgres_config = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.getenv('DB_NAME', 'provesi_db'),
            'USER': os.getenv('DB_USER', 'provesi_user'), 
            'PASSWORD': os.getenv('DB_PASSWORD', 'provesi'),
            'HOST': os.getenv('DB_HOST', '172.31.18.62'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {'connect_timeout': 10}
        }
    }
    
    sqlite_config = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
    # Fallback automático si PostgreSQL falla
    if os.getenv('FALLBACK_TO_SQLITE', 'false').lower() == 'true':
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=postgres_config['default']['HOST'],
                port=postgres_config['default']['PORT'],
                database=postgres_config['default']['NAME'],
                user=postgres_config['default']['USER'],
                password=postgres_config['default']['PASSWORD'],
                connect_timeout=5
            )
            conn.close()
            print("🐘 PostgreSQL conectado")
            return postgres_config
        except:
            print("⚠️ PostgreSQL no disponible, usando SQLite")
            return sqlite_config
    
    return postgres_config

DATABASES = get_database_config()
```

### **Opción 4: Mantener Solo PostgreSQL (Actual)**
Si mantienes la configuración actual, necesitas:

1. **Verificar conectividad al servidor**
2. **Confirmar credenciales** 
3. **Resolver problemas de red/firewall**

## 🏃‍♂️ Comandos de Diagnóstico

```bash
# Test de conectividad de red
ping 172.31.18.62

# Test de puerto PostgreSQL  
nc -zv 172.31.18.62 5432

# Test con psql (si está instalado)
psql -h 172.31.18.62 -p 5432 -U provesi_user -d provesi_db

# Test de Django
python manage.py check --database default

# Migrar cuando funcione
python manage.py migrate
```

## 📊 Recomendación

Para desarrollo y testing, sugiero **Opción 3** con configuración dual:

✅ **Mantiene PostgreSQL como principal**  
✅ **Fallback automático a SQLite si hay problemas**  
✅ **No interrumpe el desarrollo**  
✅ **Fácil cambio entre bases de datos**  

¿Quieres que implemente la configuración dual inteligente?