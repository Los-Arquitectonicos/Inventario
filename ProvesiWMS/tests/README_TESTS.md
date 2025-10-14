# Pruebas de Carga Masiva - Inventario WMS

## Resumen

Suite de pruebas para validar el requerimiento arquitectonico de carga masiva de articulos.

**Requerimiento**: Procesar 10,000 articulos en menos de 5 minutos, escalando de 100 a 2,000 req/min.

## Archivos Principales

### Scripts de Prueba
- `test_carga_simple.py` - **RECOMENDADO** Script standalone simple
- `test_carga_masiva_articulos.py` - Tests unitarios Django
- `locustfile_articulos.py` - Tests con Locust (interfaz web)

### Documentacion
- `README_SIMPLE.md` - Guia rapida de uso
- `RESUMEN_EJECUTIVO.md` - Estrategia completa
- `ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md` - Detalles tecnicos

## Inicio Rapido

### 1. Iniciar servidor
```bash
cd ProvesiWMS
python manage.py runserver
```

### 2. Ejecutar prueba principal
```bash
# En otra terminal
python tests/test_carga_simple.py
# Seleccionar opcion: 3
```

## Tests Disponibles

| Test | Cantidad | Duracion | Objetivo |
|------|----------|----------|----------|
| 1. Baseline | 100 | 30s | Linea base |
| 2. Concurrente | 1,000 | 2min | Concurrencia |
| 3. Objetivo Principal | 10,000 | 5min | Requerimiento completo |
| 4. Escalabilidad | Variable | 10min | 100 a 2,000 req/min |

## Criterios de Exito

- Tiempo total: **< 5 minutos**
- Throughput: **100 - 2,000 req/min**
- Tasa de exito: **>= 95%**
- Consistencia DB: **>= 95%**

## Resultados

Los resultados se guardan automaticamente en:
- `reporte_carga.json`

## Metricas Medidas

### Performance
- Requests por segundo
- Requests por minuto
- Tiempo total de procesamiento

### Latencia
- Minima, maxima y promedio
- Percentiles P50, P95, P99

### Confiabilidad
- Tasa de exito
- Tasa de error
- Consistencia en base de datos

## Herramientas por Caso de Uso

### Desarrollo Local
```bash
python tests/test_carga_simple.py
```
- Facil de usar
- No requiere instalacion adicional

### CI/CD
```bash
python manage.py test tests.test_carga_masiva_articulos
```
- Integrado con Django
- Falla automaticamente si no pasa

### Analisis Detallado
```bash
pip install locust
locust -f tests/locustfile_articulos.py
```
- Interfaz web
- Graficos en tiempo real
- Reportes HTML

## Estructura de Archivos

```
tests/
├── test_carga_simple.py              # Script standalone (USAR ESTE)
├── test_carga_masiva_articulos.py    # Tests Django
├── locustfile_articulos.py            # Tests Locust
├── README.md                          # Este archivo
├── README_SIMPLE.md                   # Guia rapida
├── RESUMEN_EJECUTIVO.md              # Estrategia completa
└── ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md # Detalles tecnicos
```

## Troubleshooting

### Servidor no responde
```bash
# Verificar que esta corriendo
ps aux | grep "manage.py runserver"

# Reiniciar si es necesario
python manage.py runserver
```

### Falta modulo requests
```bash
pip install requests
```

### Pruebas muy lentas
- Reducir numero de workers
- Verificar carga del sistema
- Revisar conexion a base de datos

## Proximos Pasos

1. Ejecutar test objetivo principal (test 3)
2. Revisar resultados en `reporte_carga.json`
3. Verificar que cumple todos los criterios
4. Si no cumple, optimizar y volver a probar
5. Documentar resultados finales

## Soporte

Para mas informacion, consulte:
- `README_SIMPLE.md` - Comandos y ejemplos
- `RESUMEN_EJECUTIVO.md` - Estrategia detallada
- `ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md` - Documentacion tecnica
