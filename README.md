# Sistema de Gestión de Inventario

Sistema integral de gestión de inventario con procesamiento de pedidos, desarrollado con Django y PostgreSQL.

## Características Principales

- **Gestión Completa de Inventario:** Productos, artículos, bodegas y movimientos
- **Sistema de Pedidos:** Creación y seguimiento de pedidos con asignación automática de ubicaciones
- **PostgreSQL:** Base de datos robusta para producción con respaldo SQLite
- **API RESTful:** Endpoints completos para todas las operaciones
- **Pruebas de Rendimiento:** Suite de pruebas JMeter incluida
- **Configuración Flexible:** Variables de entorno para diferentes ambientes
- **Listo para AWS:** Balanceador de carga y soporte para despliegue en la nube

## Configuración Rápida

### **Opción 1: Script Automático (Recomendado)**
```bash
# Instalar dependencias y configurar automáticamente
pip install -r requirements.txt
python setup_postgresql.py
```

### **Opción 2: Configuración Manual**

## Prerequisitos

- Python 3.8 o superior
- PostgreSQL 12 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <repository-url>
   cd Inventario
   ```

2. **Crear un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
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

**Aplicación disponible en:** `http://localhost:8000`

## Documentación Completa

- **[Configuración PostgreSQL](POSTGRESQL_README.md)** - Guía detallada de base de datos
- **[Sistema de Pedidos](PEDIDOS_README.md)** - API y funcionalidades de pedidos  
- **[Pruebas JMeter](tests/JMeter_README.md)** - Suite de pruebas de carga

## Configuración

### Configuración de Base de Datos

La aplicación utiliza PostgreSQL como base de datos predeterminada. La configuración se maneja a través de variables de entorno:

- `DB_NAME`: Nombre de la base de datos (predeterminado: inventario_db)
- `DB_USER`: Usuario de la base de datos (predeterminado: inventario_user)
- `DB_PASSWORD`: Contraseña de la base de datos
- `DB_HOST`: Host de la base de datos (predeterminado: localhost)
- `DB_PORT`: Puerto de la base de datos (predeterminado: 5432)

### Configuración de Seguridad

- `SECRET_KEY`: Clave secreta de Django para seguridad
- `DEBUG`: Modo de depuración (True/False)
- `ALLOWED_HOSTS`: Lista separada por comas de hosts permitidos

## Estructura del Proyecto

```
inventario/
├── inventario/              # Aplicación principal Django
│   ├── models.py           # Modelos: Productos, Pedidos, Artículos
│   ├── settings.py        # Configuración PostgreSQL
│   ├── urls.py             # URLs principales
│   └── views/              # Controladores API
│       ├── pedidos.py         # API de Pedidos  
│       ├── productos.py       # API de Productos
│       ├── articulos.py       # API de Artículos
│       └── bodegas.py         # API de Bodegas
├── tests/                  # Suite completa de pruebas
│   ├── inventario_load_test.jmx    # Pruebas JMeter
│   ├── test_complete_api.py         # Tests API Python
│   └── create_orders_test_data.py  # Datos de prueba
├── setup_postgresql.py     # Script de configuración automática
├── requirements.txt        # Dependencias Python
├── .env.example           # Plantilla variables de entorno
└── DOCUMENTACIÓN/
    ├── README.md              # Esta guía
    ├── PEDIDOS_README.md      # Sistema de Pedidos
    └── POSTGRESQL_README.md   # Configuración PostgreSQL
```

## Funcionalidades Principales

### **Sistema de Pedidos**
- Creación y gestión de pedidos
- Función `obtener_ubicaciones_productos()` - **Característica Principal**
- API RESTful completa (7 endpoints)
- Seguimiento automático de ubicaciones en bodega

### **Gestión de Inventario**
- Catálogo de productos con categorías
- Control de artículos individuales
- Gestión de bodegas y zonas
- Movimientos de inventario

### **Testing y Performance**
- Suite JMeter para pruebas de carga
- Tests unitarios Python
- Datos de prueba automatizados

## Desarrollo

### Ejecutar Pruebas

```bash
# Pruebas unitarias de Django
python manage.py test

# Pruebas de funcionalidad de API
python tests/api_functionality_test.py

# Pruebas de integración completas
python tests/complete_api_integration_test.py

# Pruebas de rendimiento JMeter
jmeter -n -t tests/aws_load_balancer_performance_test.jmx -l results.jtl

# Configurar datos de prueba
python tests/setup_test_data.py
```

### Pruebas de Rendimiento

```bash
# Pruebas de balanceador de carga AWS
jmeter -t tests/aws_load_balancer_performance_test.jmx

# Pruebas funcionales GUI
jmeter -t tests/pedidos_gui_functional_test.jmx

# Pruebas solo de rendimiento
jmeter -n -t tests/pedidos_performance_only_test.jmx -l performance.jtl
```

### Operaciones de Base de Datos

```bash
# Crear migraciones para cambios en modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Abrir shell de Django
python manage.py shell
```

## Despliegue en Producción

Para despliegue en producción:

1. Establecer `DEBUG=False` en tu entorno
2. Configurar apropiadamente `SECRET_KEY` y `ALLOWED_HOSTS`
3. Usar un servidor WSGI de nivel de producción como Gunicorn
4. Configurar el servicio de archivos estáticos
5. Establecer seguridad apropiada para PostgreSQL

## Licencia

[Add your license information here]