# Guia Rapida - Pruebas de Carga Masiva

## Inicio Rapido

### 1. Iniciar el servidor
```bash
cd ProvesiWMS
python manage.py runserver
```

### 2. Ejecutar pruebas (terminal separada)
```bash
cd ProvesiWMS
python tests/test_carga_simple.py
```

Seleccione la opcion 3 para el test objetivo principal.

## Tests Disponibles

### Test 1: Baseline (100 articulos)
- Duracion: ~30 segundos
- Modo: Secuencial
- Objetivo: Establecer linea base

```bash
python tests/test_carga_simple.py
# Seleccionar opcion: 1
```

### Test 2: Concurrente (1,000 articulos)
- Duracion: ~2 minutos
- Workers: 10
- Objetivo: Validar concurrencia

```bash
python tests/test_carga_simple.py
# Seleccionar opcion: 2
```

### Test 3: Objetivo Principal (10,000 articulos)
- Duracion: ~5 minutos
- Workers: 50
- Objetivo: Validar requerimiento completo

```bash
python tests/test_carga_simple.py
# Seleccionar opcion: 3
```

### Test 4: Escalabilidad
- Duracion: ~10 minutos
- Objetivo: Validar escalamiento de 100 a 2,000 req/min

```bash
python tests/test_carga_simple.py
# Seleccionar opcion: 4
```

## Criterios de Aceptacion

| Metrica | Objetivo |
|---------|----------|
| Tiempo total | < 5 minutos |
| Throughput minimo | 100 req/min |
| Throughput maximo | 2,000 req/min |
| Tasa de exito | >= 95% |
| Consistencia DB | >= 95% |

## Resultados

Los resultados se guardan en:
- `reporte_carga.json` - Resultados detallados en JSON

### Ejemplo de resultado exitoso:
```json
{
  "test": "objetivo_10000",
  "cantidad": 10000,
  "exitosos": 9523,
  "tiempo_total": 291.5,
  "req_por_minuto": 2058,
  "tasa_exito": 95.23,
  "cumple_tiempo": true,
  "cumple_tasa": true
}
```

## Troubleshooting

### Error: No se puede conectar al servidor
```bash
# Verificar que el servidor esta corriendo
cd ProvesiWMS
python manage.py runserver
```

### Error: pip module not found
```bash
pip install requests
```

### Pruebas muy lentas
- Reducir cantidad de workers
- Verificar carga del sistema
- Revisar conexion a base de datos

## Herramientas Alternativas

### Usar Django Tests
```bash
python manage.py test tests.test_carga_masiva_articulos.TestCargaMasivaArticulos.test_03_carga_10000_articulos_objetivo_principal -v 2
```

### Usar Locust (interfaz web)
```bash
pip install locust
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000
# Abrir: http://localhost:8089
```

## Comandos Utiles

### Ver procesos Django
```bash
ps aux | grep manage.py
```

### Ver uso de puertos
```bash
lsof -i :8000
```

### Limpiar base de datos de prueba
```bash
python manage.py shell
>>> from inventario.models import Articulo
>>> Articulo.objects.filter(codigo_barras__startswith='7898').delete()
```

## Interpretacion de Resultados

### Throughput
- **100-500 req/min**: Carga baja, aceptable para operacion normal
- **500-1000 req/min**: Carga media, buena capacidad
- **1000-2000 req/min**: Carga alta, cumple objetivo maximo

### Latencia
- **< 100ms**: Excelente
- **100-500ms**: Aceptable
- **500-1000ms**: Alto, revisar optimizaciones
- **> 1000ms**: Critico, requiere atencion

### Tasa de Exito
- **>= 95%**: Aceptable
- **90-95%**: Revisar errores
- **< 90%**: Critico, investigar fallas

## Proximos Pasos

1. Ejecutar test objetivo principal (opcion 3)
2. Verificar que cumple criterios
3. Si no cumple, analizar:
   - Aumentar workers
   - Optimizar queries en Django
   - Verificar capacidad del servidor
4. Documentar resultados
5. Implementar en produccion
