# 🏪 Sistema de Inventario y Pedidos

Sistema integral de gestión de inventario con manejo de pedidos, desarrollado en Django con base de datos PostgreSQL.

## ✨ Características Principales

- **🎯 Gestión Completa de Inventario:** Productos, artículos, bodegas y movimientos
- **📦 Sistema de Pedidos:** Creación y seguimiento de pedidos con ubicaciones automáticas
- **🐘 PostgreSQL:** Base de datos robusta para producción
- **🔧 API RESTful:** Endpoints completos para todas las operaciones
- **⚡ JMeter Testing:** Suite de pruebas de carga incluida
- **🌍 Configuración Flexible:** Variables de entorno para diferentes ambientes

## 🚀 Configuración Rápida

### **Opción 1: Script Automático (Recomendado)**
```bash
# Instalar dependencias y configurar automáticamente
pip install -r requirements.txt
python setup_postgresql.py
```

### **Opción 2: Configuración Manual**

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Inventario
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar PostgreSQL:**
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales de PostgreSQL
   ```

5. **Ejecutar migraciones:**
   ```bash
   python manage.py migrate
   ```

6. **Iniciar servidor:**
   ```bash
   python manage.py runserver
   ```

🌐 **Aplicación disponible en:** `http://localhost:8000`

## 📋 Documentación Completa

- **📖 [Configuración PostgreSQL](POSTGRESQL_README.md)** - Guía detallada de base de datos
- **🎯 [Sistema de Pedidos](PEDIDOS_README.md)** - API y funcionalidades de pedidos  
- **⚡ [Pruebas JMeter](tests/JMeter_README.md)** - Suite de pruebas de carga

## Configuration

### Database Settings

The application uses PostgreSQL as the default database. Configuration is handled through environment variables:

- `DB_NAME`: Database name (default: inventario_db)
- `DB_USER`: Database user (default: inventario_user)
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)

### Security Settings

- `SECRET_KEY`: Django secret key for security
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## 📁 Estructura del Proyecto

```
inventario/
├── 🏪 inventario/              # Aplicación principal Django
│   ├── 📝 models.py           # Modelos: Productos, Pedidos, Artículos
│   ├── ⚙️  settings.py        # Configuración PostgreSQL
│   ├── 🌐 urls.py             # URLs principales
│   └── 📂 views/              # Controladores API
│       ├── pedidos.py         # 📦 API de Pedidos  
│       ├── productos.py       # 🏷️  API de Productos
│       ├── articulos.py       # 📋 API de Artículos
│       └── bodegas.py         # 🏬 API de Bodegas
├── 🧪 tests/                  # Suite completa de pruebas
│   ├── ⚡ inventario_load_test.jmx    # Pruebas JMeter
│   ├── 📊 test_complete_api.py         # Tests API Python
│   └── 📋 create_orders_test_data.py  # Datos de prueba
├── 🐘 setup_postgresql.py     # Script de configuración automática
├── 📋 requirements.txt        # Dependencias Python
├── 🔧 .env.example           # Plantilla variables de entorno
└── 📖 DOCUMENTACIÓN/
    ├── README.md              # Esta guía
    ├── PEDIDOS_README.md      # Sistema de Pedidos
    └── POSTGRESQL_README.md   # Configuración PostgreSQL
```

## 🎯 Funcionalidades Principales

### **📦 Sistema de Pedidos**
- ✅ Creación y gestión de pedidos
- ✅ Función `obtener_ubicaciones_productos()` - **Característica Principal**
- ✅ API RESTful completa (7 endpoints)
- ✅ Seguimiento automático de ubicaciones en bodega

### **🏪 Gestión de Inventario**
- ✅ Catálogo de productos con categorías
- ✅ Control de artículos individuales
- ✅ Gestión de bodegas y zonas
- ✅ Movimientos de inventario

### **⚡ Testing y Performance**
- ✅ Suite JMeter para pruebas de carga
- ✅ Tests unitarios Python
- ✅ Datos de prueba automatizados

## Development

### Running Tests

```bash
python manage.py test
```

### Checking Code Quality

```bash
python manage.py check
```

### Database Operations

```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Django shell
python manage.py shell
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Configure proper `SECRET_KEY` and `ALLOWED_HOSTS`
3. Use a production-grade WSGI server like Gunicorn
4. Configure static files serving
5. Set up proper PostgreSQL security

## License

[Add your license information here]