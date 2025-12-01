# Indice Rapido de Pruebas - ProvesiWMS

## Ejecucion Rapida

### Pruebas de Seguridad
```bash
# Navegar a la carpeta
cd tests/seguridad

# Importar colecciones en Postman:
# 1. Anti_Modificacion_Pedidos_Atacante.postman_collection.json
# 2. Security_Tests_Atacante.postman_collection.json  
# 3. Anti_Modificacion_API_Pedidos.postman_collection.json
# 4. Legitimate_User_Tests.postman_collection.json
# 5. Security_Validation_Corrected.postman_collection.json

# Configurar variable 'base_url' en Postman con tu servidor
# Ejecutar collections en Postman
```

### Pruebas de Escalabilidad
```bash
# Navegar a la carpeta
cd tests/escalabilidad

# Instalar Locust (si es necesario)
pip install locust

# Configurar URL en config_entornos.py
# Ejecutar todas las pruebas
./run_load_tests.sh all

# O prueba específica
./run_load_tests.sh objective
```

## Archivos por Categoria

### Seguridad (5 colecciones Postman)
- **Anti_Modificacion_Pedidos_Atacante** - Ataques a pedidos
- **Security_Tests_Atacante** - Suite completa de ataques
- **Anti_Modificacion_API_Pedidos** - Ataques a API REST
- **Legitimate_User_Tests** - Validación usuarios legítimos
- **Security_Validation_Corrected** - Validación general

### Escalabilidad (Locust + Reportes)
- **locustfile.py** - Escenarios de carga
- **run_load_tests.sh** - Script de ejecución
- **config_entornos.py** - Configuración de URLs
- **reportes/** - Resultados de pruebas ejecutadas

## Objetivos de Validacion

### Seguridad: 100% Proteccion
- Ningún atacante puede modificar pedidos sin autenticación
- Todos los ataques deben fallar (códigos 401/403)
- Sistema rechaza tokens falsos y inyecciones

### Escalabilidad: 100-2000 req/min
- Capacidad de 100 a 2,000 peticiones por minuto
- 10,000 registros procesados en menos de 5 minutos
- Tasa de éxito >= 95%

---
Ver README.md en cada carpeta para documentación detallada.