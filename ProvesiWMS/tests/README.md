# Tests - ProvesiWMS

Este directorio contiene todas las pruebas automatizadas para el sistema ProvesiWMS, organizadas por categorías específicas.

## Estructura Organizacional

### 📁 `/seguridad/`
**Pruebas de seguridad, autenticación y autorización**
- Simulación de ataques de seguridad
- Validación de protección contra acceso no autorizado
- Verificación de medidas de seguridad implementadas
- [Ver documentación detallada](./seguridad/README.md)

**Archivos principales:**
- `Anti_Modificacion_Pedidos_Atacante.postman_collection.json`
- `Security_Tests_Atacante.postman_collection.json`
- `Anti_Modificacion_API_Pedidos.postman_collection.json`
- `Legitimate_User_Tests.postman_collection.json`
- `Security_Validation_Corrected.postman_collection.json`

### 📁 `/escalabilidad/`
**Pruebas de carga, rendimiento y escalabilidad**
- Pruebas de estrés con Locust
- Análisis de capacity planning
- Métricas de rendimiento bajo carga
- [Ver documentación detallada](./escalabilidad/README.md)

**Archivos principales:**
- `locustfile.py` - Definición de escenarios de carga
- `config_entornos.py` - Configuración de entornos
- `run_load_tests.sh` - Script de ejecución automatizada
- `reportes/` - Reportes de pruebas ejecutadas

## Requisito de Escalabilidad (ASR)

**Contexto:** Como personal administrativo de Provesi, dado que el ambiente está sobrecargado con la apertura de nuevas bodegas, cuando realizo operaciones de carga masiva de inventario, quiero que el sistema incremente su capacidad de procesamiento desde 100 peticiones por minuto hasta 2,000 peticiones por minuto, asegurando que cada carga de 10,000 registros se complete en menos de 5 minutos conforme crece la demanda.

**Objetivos:**
- Throughput: 100 a 2,000 peticiones/minuto
- Capacidad: 10,000 registros en menos de 5 minutos
- Tasa de éxito: >= 95%

## Requisito de Seguridad

**Contexto:** Yo como Atacante cuando trate de modificar la información de los pedidos dado que el sistema está en línea se espera que el atacante no pueda modificar la información y esto debe suceder el 100%

**Objetivos:**
- 100% bloqueo de acceso sin autenticación
- Protección completa contra modificación no autorizada
- Validación de medidas de seguridad implementadas

## Ejecución Rápida

### Pruebas de Seguridad
```bash
cd tests/seguridad
# Importar colecciones en Postman y ejecutar
```

### Pruebas de Escalabilidad
```bash
cd tests/escalabilidad
./run_load_tests.sh all
```

## Archivos de Soporte

- `.gitignore` - Exclusiones de Git
- `__pycache__/` - Cache de Python (auto-generado)

---

**Nota:** Cada categoría tiene su propia documentación detallada con instrucciones específicas de instalación, configuración y ejecución.

