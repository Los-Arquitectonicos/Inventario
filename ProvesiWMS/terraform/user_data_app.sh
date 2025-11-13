#!/bin/bash

# Log de instalación
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "=========================================="
echo "CONFIGURANDO SERVIDOR APP ${SERVER_INDEX}"
echo "$(date): Iniciando configuración automática..."
echo "=========================================="

# ===================================
# CONFIGURAR VARIABLES DE ENTORNO
# ===================================

echo "$(date): Configurando variables de entorno..."

# Variables de entorno para Django y autenticación
cat >> /etc/environment << EOF
DATABASE_HOST=${DATABASE_HOST_PLACEHOLDER}
DATABASE_NAME=provesi_wms
DATABASE_USER=provesi_user
DATABASE_PASSWORD=provesi_password_2024
DATABASE_PORT=5432
SECRET_KEY=django-insecure-test-key-2024
DEBUG=True
DJANGO_SETTINGS_MODULE=wms.settings
ALLOWED_HOSTS=*
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
JWT_ALGORITHM=HS256
CORS_ALLOW_ALL_ORIGINS=True
EOF

# Recargar variables de entorno
source /etc/environment

# ===================================
# INSTALAR DEPENDENCIAS DEL SISTEMA
# ===================================

echo "$(date): Actualizando sistema e instalando dependencias..."

# Actualizar sistema
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# Instalar dependencias base
apt-get install -y \
  python3-pip \
  python3-venv \
  git \
  build-essential \
  libpq-dev \
  python3-dev \
  nginx \
  curl \
  wget \
  postgresql-client

echo "$(date): Dependencias del sistema instaladas"

# ===================================
# INSTALAR DEPENDENCIAS PYTHON
# ===================================

echo "$(date): Instalando dependencias Python..."

# Actualizar pip e instalar paquetes (manejar entorno externamente administrado)
pip3 install --upgrade pip --break-system-packages 2>/dev/null || pip3 install --upgrade pip
pip3 install --break-system-packages \
  django==4.2.24 \
  psycopg2-binary \
  djangorestframework \
  djangorestframework-simplejwt \
  django-cors-headers \
  gunicorn || \
pip3 install \
  django==4.2.24 \
  psycopg2-binary \
  djangorestframework \
  djangorestframework-simplejwt \
  django-cors-headers \
  gunicorn

echo "$(date): Dependencias Python instaladas"

# Verificar instalación de Django
python3 -c "import django; print('Django version:', django.get_version())" || {
  echo "$(date): ERROR - Django no se instaló correctamente"
  exit 1
}

# ===================================
# CONFIGURAR APLICACIÓN DJANGO
# ===================================

echo "$(date): Configurando aplicación Django..."

# Crear directorio de aplicaciones
mkdir -p /opt/apps
chown ubuntu:ubuntu /opt/apps
cd /opt/apps

# Clonar repositorio
echo "$(date): Clonando repositorio..."
if [ -d Inventario ]; then
  rm -rf Inventario
fi

git clone https://github.com/Los-Arquitectonicos/Inventario.git || {
  echo "$(date): ERROR - No se pudo clonar repositorio"
  exit 1
}

cd Inventario
echo "$(date): Cambiando a branch Sprint3V2..."
git fetch origin Sprint3V2 || echo "$(date): Warning: No se pudo hacer fetch"
git checkout Sprint3V2 || echo "$(date): Warning: Usando branch por defecto"

# Navegar al proyecto Django
cd ProvesiWMS

# Verificar archivos
echo "$(date): Verificando archivos de Django..."
if [ ! -f manage.py ]; then
  echo "$(date): ERROR - manage.py no encontrado"
  ls -la
  exit 1
fi

# ===================================
# CONFIGURAR BASE DE DATOS
# ===================================

echo "$(date): Configurando base de datos..."

# Esperar a que PostgreSQL esté disponible
DB_HOST="${DATABASE_HOST_PLACEHOLDER}"
DB_PORT="5432"
DB_USER="provesi_user"

echo "$(date): Esperando conexión a base de datos $DB_HOST:$DB_PORT..."

RETRY_COUNT=0
MAX_RETRIES=30
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" 2>/dev/null; then
    echo "$(date): Base de datos disponible"
    break
  else
    echo "$(date): Esperando BD... intento $((RETRY_COUNT + 1))/$MAX_RETRIES"
    sleep 10
    RETRY_COUNT=$((RETRY_COUNT + 1))
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "$(date): WARNING: Base de datos no disponible, continuando..."
fi

# Aplicar migraciones (solo en la primera instancia)
if [ "$SERVER_INDEX" = "1" ]; then
  echo "$(date): Aplicando migraciones en servidor principal..."
  python3 manage.py makemigrations --noinput || echo "$(date): Warning: Error en makemigrations"
  python3 manage.py migrate --noinput || echo "$(date): Warning: Error en migrate"
  
  # Configurar usuarios iniciales
  if [ -f setup_users.py ]; then
    echo "$(date): Configurando usuarios iniciales..."
    python3 setup_users.py || echo "$(date): Warning: Error configurando usuarios"
  fi
  
  # Recolectar archivos estáticos
  echo "$(date): Recolectando archivos estáticos..."
  python3 manage.py collectstatic --noinput || echo "$(date): Warning: Error en collectstatic"
else
  echo "$(date): Servidor secundario - esperando migraciones..."
  sleep 120
fi

# ===================================
# CONFIGURAR NGINX
# ===================================

echo "$(date): Configurando Nginx..."

# Configurar Nginx
tee /etc/nginx/sites-available/provesi-wms > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/apps/Inventario/ProvesiWMS/static/;
        expires 1y;
    }
}
EOF

# Habilitar sitio
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/provesi-wms /etc/nginx/sites-enabled/

# Verificar y reiniciar nginx
nginx -t && systemctl restart nginx || echo "$(date): Warning: Error configurando Nginx"
systemctl enable nginx

# ===================================
# CREAR SCRIPTS DE UTILIDAD
# ===================================

echo "$(date): Creando scripts de utilidad..."

# Script para iniciar Django
tee /home/ubuntu/start-django.sh > /dev/null <<'EOF'
#!/bin/bash
echo "Iniciando ProvesiWMS..."
cd /opt/apps/Inventario/ProvesiWMS
source /etc/environment
python3 manage.py runserver 0.0.0.0:8000
EOF

chmod +x /home/ubuntu/start-django.sh
chown ubuntu:ubuntu /home/ubuntu/start-django.sh

# Script de debug
tee /home/ubuntu/debug.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=== DEBUG PROVESI WMS ==="
echo "Fecha: $(date)"
echo ""
echo "=== Django instalado? ==="
python3 -c "import django; print('Django version:', django.get_version())" || echo "Django NO instalado"
echo ""
echo "=== Variables de entorno ==="
env | grep -E "DATABASE|SECRET|DEBUG" | sort
echo ""
echo "=== Archivos aplicación ==="
ls -la /opt/apps/Inventario/ProvesiWMS/
echo ""
echo "=== Logs user-data ==="
tail -20 /var/log/user-data.log
EOF

chmod +x /home/ubuntu/debug.sh
chown ubuntu:ubuntu /home/ubuntu/debug.sh

echo "=========================================="
echo "$(date): ✅ CONFIGURACIÓN COMPLETADA"
echo "Servidor: $SERVER_INDEX"
echo "IP: $(hostname -I | awk '{print $1}')"
echo "Para iniciar Django: ./start-django.sh"
echo "Para debug: ./debug.sh"
echo "=========================================="