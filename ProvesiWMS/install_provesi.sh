#!/bin/bash

# Script de instalación manual para ProvesiWMS en EC2
# Ejecutar como: curl -L https://raw.githubusercontent.com/Los-Arquitectonicos/Inventario/Sprint3V2/ProvesiWMS/install_provesi.sh | bash

set -e  # Exit on error

echo "=========================================="
echo "INSTALACIÓN MANUAL PROVESI WMS"
echo "$(date)"
echo "=========================================="

# Función para imprimir mensajes
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Verificar si es la primera instancia (parámetro opcional)
IS_PRIMARY=${1:-"true"}

log "Iniciando instalación..."

# ===================================
# ACTUALIZAR SISTEMA E INSTALAR DEPENDENCIAS
# ===================================

log "Actualizando sistema..."
sudo apt-get update -y

log "Instalando dependencias del sistema..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    libpq-dev \
    build-essential \
    postgresql-client \
    git \
    curl \
    nginx

# ===================================
# INSTALAR DEPENDENCIAS PYTHON
# ===================================

log "Instalando dependencias Python..."
sudo pip3 install --upgrade pip

# Verificar si el entorno está externamente administrado
if pip3 install django==4.2.24 --dry-run 2>&1 | grep -q "externally-managed-environment"; then
    log "Entorno Python externamente administrado detectado, usando --break-system-packages"
    sudo pip3 install --break-system-packages \
        django==4.2.24 \
        psycopg2-binary \
        djangorestframework \
        djangorestframework-simplejwt \
        django-cors-headers \
        gunicorn
else
    log "Instalando paquetes Python normalmente"
    sudo pip3 install \
        django==4.2.24 \
        psycopg2-binary \
        djangorestframework \
        djangorestframework-simplejwt \
        django-cors-headers \
        gunicorn
fi

log "Verificando instalación de Django..."
python3 -c "import django; print('Django version:', django.get_version())"

# ===================================
# CLONAR REPOSITORIO
# ===================================

log "Configurando aplicación..."
cd ~

if [ -d "Inventario" ]; then
    log "Repositorio ya existe, actualizando..."
    cd Inventario
    git pull origin Sprint3V2
else
    log "Clonando repositorio..."
    git clone https://github.com/Los-Arquitectonicos/Inventario.git
    cd Inventario
    git checkout Sprint3V2
fi

cd ProvesiWMS

# ===================================
# CONFIGURAR VARIABLES DE ENTORNO
# ===================================

log "Configurando variables de entorno..."

# Intentar obtener variables desde /etc/environment (si fueron configuradas por Terraform)
if [ -f "/etc/environment" ]; then
    source /etc/environment
    log "Variables cargadas desde /etc/environment"
else
    log "Configurando variables por defecto..."
fi

# Configurar variables si no están definidas
export DATABASE_HOST=${DATABASE_HOST:-"127.0.0.1"}
export DATABASE_NAME=${DATABASE_NAME:-"provesi_wms"}
export DATABASE_USER=${DATABASE_USER:-"provesi_user"}
export DATABASE_PASSWORD=${DATABASE_PASSWORD:-"provesi_password_2024"}
export SECRET_KEY=${SECRET_KEY:-"django-insecure-test-key-2024"}
export DEBUG=${DEBUG:-"True"}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"wms.settings"}

log "Variables de entorno configuradas:"
echo "  DATABASE_HOST: $DATABASE_HOST"
echo "  DATABASE_NAME: $DATABASE_NAME"
echo "  DATABASE_USER: $DATABASE_USER"

# ===================================
# CONFIGURAR BASE DE DATOS
# ===================================

if [ "$IS_PRIMARY" = "true" ]; then
    log "Esta es la instancia principal, aplicando migraciones..."
    
    # Esperar a que la base de datos esté disponible
    log "Verificando conectividad a la base de datos..."
    RETRY_COUNT=0
    MAX_RETRIES=10
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if pg_isready -h "$DATABASE_HOST" -p 5432 -U "$DATABASE_USER" 2>/dev/null; then
            log "Base de datos disponible"
            break
        else
            log "Esperando base de datos... intento $((RETRY_COUNT + 1))/$MAX_RETRIES"
            sleep 10
            RETRY_COUNT=$((RETRY_COUNT + 1))
        fi
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log "WARNING: No se pudo conectar a la base de datos, continuando..."
    fi
    
    # Aplicar migraciones
    log "Aplicando migraciones..."
    python3 manage.py migrate --noinput || log "ERROR en migraciones, continuando..."
    
    # Configurar usuarios
    log "Configurando usuarios iniciales..."
    python3 setup_users.py || log "ERROR configurando usuarios, continuando..."
    
    # Recopilar archivos estáticos
    log "Recopilando archivos estáticos..."
    python3 manage.py collectstatic --noinput || log "ERROR en collectstatic, continuando..."
else
    log "Instancia secundaria, esperando a que la principal complete las migraciones..."
    sleep 60
fi

# ===================================
# CONFIGURAR NGINX (OPCIONAL)
# ===================================

log "Configurando Nginx..."
sudo tee /etc/nginx/sites-available/provesi > /dev/null << 'EOF'
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
        alias /home/ubuntu/Inventario/ProvesiWMS/static/;
        expires 1y;
    }
}
EOF

# Habilitar sitio
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/provesi /etc/nginx/sites-enabled/

# Reiniciar nginx
sudo nginx -t && sudo systemctl restart nginx || log "ERROR configurando Nginx"

# ===================================
# CREAR SCRIPTS DE UTILIDAD
# ===================================

log "Creando scripts de utilidad..."

# Script para iniciar Django
cat > ~/start-provesi.sh << 'EOF'
#!/bin/bash
echo "Iniciando ProvesiWMS..."
cd ~/Inventario/ProvesiWMS

# Cargar variables de entorno
export DATABASE_HOST="${DATABASE_HOST:-127.0.0.1}"
export DATABASE_NAME="${DATABASE_NAME:-provesi_wms}"
export DATABASE_USER="${DATABASE_USER:-provesi_user}"
export DATABASE_PASSWORD="${DATABASE_PASSWORD:-provesi_password_2024}"
export SECRET_KEY="${SECRET_KEY:-django-insecure-test-key-2024}"
export DEBUG="${DEBUG:-True}"

echo "Iniciando servidor en puerto 8000..."
python3 manage.py runserver 0.0.0.0:8000
EOF

chmod +x ~/start-provesi.sh

# Script de debug
cat > ~/debug-provesi.sh << 'EOF'
#!/bin/bash
echo "=== DEBUG PROVESI WMS ==="
echo "Fecha: $(date)"
echo ""

echo "=== Verificar Django ==="
python3 -c "import django; print('Django version:', django.get_version())" 2>/dev/null || echo "ERROR: Django no instalado"

echo ""
echo "=== Variables de entorno ==="
env | grep -E "DATABASE|SECRET|DEBUG" | sort

echo ""
echo "=== Archivos de aplicación ==="
ls -la ~/Inventario/ProvesiWMS/ 2>/dev/null || echo "Directorio no encontrado"

echo ""
echo "=== Estado de servicios ==="
ps aux | grep -E "manage.py|runserver" | grep -v grep

echo ""
echo "=== Test conexión BD ==="
pg_isready -h "${DATABASE_HOST:-127.0.0.1}" -p 5432 -U "${DATABASE_USER:-provesi_user}" 2>/dev/null || echo "BD no accesible"

echo ""
echo "=== Para iniciar Django ==="
echo "cd ~/Inventario/ProvesiWMS && python3 manage.py runserver 0.0.0.0:8000"
EOF

chmod +x ~/debug-provesi.sh

# ===================================
# FINALIZACIÓN
# ===================================

log "=========================================="
log "✅ INSTALACIÓN COMPLETADA"
log "Directorio: ~/Inventario/ProvesiWMS"
log "Para iniciar: ./start-provesi.sh"
log "Para debug: ./debug-provesi.sh"
log "Para iniciar manualmente:"
log "  cd ~/Inventario/ProvesiWMS"
log "  python3 manage.py runserver 0.0.0.0:8000"
log "=========================================="