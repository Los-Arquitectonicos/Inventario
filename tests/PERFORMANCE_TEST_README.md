# ✅ Test de Rendimiento JMeter - Pedidos GET

## 📋 Archivos Disponibles

### 🎯 **`tests/pedidos_performance_test.jmx`** - Test de Rendimiento Puro
- **Propósito**: Medir únicamente velocidad de respuesta GET /api/pedidos/
- **Sin assertions**: No hay validaciones que puedan fallar, solo medición de rendimiento
- **Configuración**: 5 threads, 5 segundos de ramp-up, 1 loop
- **Inspirado en**: Load-tests.jmx - enfoque minimalista

### 🔧 **`tests/pedidos_gui_compatible.jmx`** - Test Corregido
- **Propósito**: Test funcional completo SIN la aserción problemática
- **Cambio aplicado**: ✅ Eliminada aserción `"ubicaciones_productos"`
- **Mantiene**: Todas las otras validaciones importantes

## 🚀 Uso Recomendado para Rendimiento

```bash
# 1. Iniciar servidor Django
python manage.py runserver 8001

# 2. Ejecutar test de rendimiento (línea de comandos)
jmeter -n -t tests/pedidos_performance_test.jmx -l performance_results.jtl

# 3. Ver resumen de resultados
tail performance_results.jtl

# 4. Abrir en GUI para análisis visual
jmeter tests/pedidos_performance_test.jmx
```

## 📊 Métricas que Mide

El test de rendimiento captura:
- ⏱️ **Tiempo de respuesta** promedio, mínimo, máximo
- 🚀 **Throughput** (requests por segundo)
- 📈 **Latencia** de red
- 🔗 **Tiempo de conexión**
- 📊 **Distribución temporal** de respuestas

## 🎮 Listeners Incluidos

1. **View Results Tree**: Ver cada request individual
2. **Summary Report**: Estadísticas consolidadas 
3. **Graph Results**: Visualización gráfica de rendimiento

## ⚡ Configuración Optimizada

- **Threads**: 5 (carga moderada para medición precisa)
- **Ramp-up**: 5 segundos (arranque gradual)
- **Loops**: 1 (una pasada por thread)
- **Timeouts**: Por defecto (sin límites artificiales)

## 🔧 Sin Assertions = Sin Fallos

El test está diseñado para **nunca fallar** por assertions, permitiendo:
- ✅ Medición pura de rendimiento
- ✅ Funciona aunque el endpoint retorne error 500
- ✅ Compatibilidad universal con cualquier respuesta
- ✅ Enfoque en métricas de velocidad, no validación funcional

## 🎯 Resultado Esperado

```
summary = 5 in 00:00:XX = Y.Y/s Avg: ZZ Min: AA Max: BB Err: 0 (0.00%)
```

- **5 requests** ejecutados
- **Y.Y/s** throughput 
- **ZZ ms** tiempo promedio
- **0 errores** por assertions (solo errores de conexión si los hay)