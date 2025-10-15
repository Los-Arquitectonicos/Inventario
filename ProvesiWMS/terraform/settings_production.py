# Configuración para producción con PostgreSQL
# Este archivo muestra cómo actualizar settings.py para usar PostgreSQL en AWS

import os

# IMPORTANTE: En producción, usa variables de entorno para SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-k5*egyc&n_03(l8d1ix7_cx7si0e^3^5+qg_#he$^+a$8xawr7')

# En producción, cambiar a False
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Permitir acceso desde el ALB y los servidores
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.elb.amazonaws.com',  # Permite cualquier ALB de AWS
    '*',  # En producción, especificar dominios exactos
]

# Base de datos: PostgreSQL en producción, SQLite en desarrollo
if os.environ.get('DATABASE_HOST'):
    # Configuración para PostgreSQL (AWS)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DATABASE_NAME', 'inventario_db'),
            'USER': os.environ.get('DATABASE_USER', 'inventario_user'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'inventario2024'),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT', '5432'),
            'CONN_MAX_AGE': 600,  # Mantener conexiones por 10 minutos
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }
else:
    # Configuración para SQLite (desarrollo local)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Configuración de archivos estáticos para producción
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Seguridad en producción
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Cambiar a True si usas HTTPS
    SESSION_COOKIE_SECURE = False  # Cambiar a True si usas HTTPS
    CSRF_COOKIE_SECURE = False  # Cambiar a True si usas HTTPS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Logging para producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
