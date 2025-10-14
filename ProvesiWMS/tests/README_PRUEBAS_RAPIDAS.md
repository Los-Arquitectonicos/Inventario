# 🚀 Guía Rápida - Pruebas de Carga Masiva

## ⚡ Inicio Rápido (5 minutos)

### 1. Preparar el Entorno

```bash
# Terminal 1: Iniciar servidor Django
cd /Users/pedropablosanintrujillo/GitHub/Inventario/ProvesiWMS
python manage.py runserver

# Terminal 2: Ejecutar pruebas
cd /Users/pedropablosanintrujillo/GitHub/Inventario/ProvesiWMS
python tests/test_carga_standalone.py
```

### 2. Seleccionar Prueba

Cuando se le presente el menú, seleccione:
- **Opción 3**: Para ejecutar el test objetivo de 10,000 artículos

---

## 🎯 Comandos Esenciales

### Opción A: Script Standalone (RECOMENDADO - Más fácil)

```bash
# Ejecutar con menú interactivo
python tests/test_carga_standalone.py
```

**Ventajas**:
- ✅ Menú interactivo
- ✅ Colores y progreso visual
- ✅ No requiere configuración adicional
- ✅ Genera reporte JSON automáticamente

---

### Opción B: Django Tests (Para integración)

```bash
# Test objetivo principal (10,000 artículos)
python manage.py test tests.test_carga_masiva_articulos.TestCargaMasivaArticulos.test_03_carga_10000_articulos_objetivo_principal -v 2

# Todas las pruebas
python manage.py test tests.test_carga_masiva_articulos -v 2
```

---

### Opción C: Locust (Para gráficos y reportes avanzados)

```bash
# Instalar locust primero
pip install locust

# Ejecutar con interfaz web
locust -f tests/locustfile_articulos.py --host=http://127.0.0.1:8000

# Abrir navegador en: http://localhost:8089
# Configurar: 35 users, spawn rate 7, run time 5m
```

**Ejecutar sin interfaz (headless)**:
```bash
# Test objetivo: 10,000 artículos en 5 minutos
locust -f tests/locustfile_articulos.py \
       --host=http://127.0.0.1:8000 \
       --users 35 \
       --spawn-rate 7 \
       --run-time 5m \
       --headless \
       --html reporte_locust.html
```

---

## 📊 Interpretación de Resultados

### ✅ Prueba EXITOSA si:
```
✓ Tiempo total ≤ 300 segundos (5 minutos)
✓ Throughput entre 100-2,000 req/min
✓ Tasa de éxito ≥ 95%
✓ Consistencia en DB ≥ 95%
```

### Ejemplo de salida exitosa:
```
📊 RESULTADOS FINALES
✅ CARGA COMPLETADA:
  Total artículos: 10,000
  Exitosos: 9,523 (95.23%)
  Fallidos: 477

⏱️  TIEMPOS:
  Tiempo total: 291.50s (4.86 min)
  ✅ CUMPLE el objetivo de tiempo

📈 THROUGHPUT:
  Requests/minuto: 2,058
  ✅ DENTRO del rango objetivo
```

---

## 🔍 Archivos Generados

Después de ejecutar las pruebas, se generan:

```
ProvesiWMS/
├── reporte_carga_masiva.json    # Reporte detallado en JSON
├── reporte_locust.html          # Reporte Locust (si usó Locust)
└── tests/
    └── *.pyc                     # Archivos compilados
```

### Ver reporte JSON:
```bash
cat reporte_carga_masiva.json | python -m json.tool
```

---

## ⚠️ Troubleshooting Rápido

### Error: "No se puede conectar al servidor"
**Solución**:
```bash
# Verificar que Django está corriendo
curl http://127.0.0.1:8000/inventario/

# Si no responde, iniciar servidor:
python manage.py runserver
```

### Error: "ModuleNotFoundError: No module named 'requests'"
**Solución**:
```bash
pip install requests
```

### Error: "ModuleNotFoundError: No module named 'locust'"
**Solución**:
```bash
pip install locust
```

### Throughput muy bajo
**Solución**: Ajustar número de workers:
```python
# En test_carga_standalone.py, línea ~260
workers = 50  # Aumentar a 70-100 si el servidor soporta
```

---

## 📈 Configuraciones Recomendadas por Escenario

### Desarrollo Local (MacBook Pro)
```python
workers = 30-50
cantidad = 10000
timeout = 30
```

### Servidor Dedicado
```python
workers = 50-100
cantidad = 10000
timeout = 60
```

### Producción (con load balancer)
```python
workers = 100-200
cantidad = 50000
timeout = 30
```

---

## 🎯 Checklist Pre-Ejecución

- [ ] Servidor Django corriendo en puerto 8000
- [ ] Base de datos tiene productos (>50)
- [ ] Base de datos tiene ubicaciones (>1)
- [ ] Python 3.9+ instalado
- [ ] Librería `requests` instalada
- [ ] Espacio suficiente en disco (~500MB)
- [ ] Memoria RAM disponible (~2GB)

---

## 📞 Comandos de Verificación Rápida

```bash
# Verificar productos en DB
python manage.py shell -c "from inventario.models import Producto; print(f'Productos: {Producto.objects.count()}')"

# Verificar ubicaciones en DB
python manage.py shell -c "from inventario.models import UbicacionBodega; print(f'Ubicaciones: {UbicacionBodega.objects.count()}')"

# Verificar servidor
curl -I http://127.0.0.1:8000/inventario/

# Ver últimos artículos creados
python manage.py shell -c "from inventario.models import Articulo; print(f'Artículos totales: {Articulo.objects.count()}')"
```

---

## 🚀 Ejecución en Una Línea

### Prueba Completa Automatizada:
```bash
cd ProvesiWMS && python tests/test_carga_standalone.py <<< "3"
```

### Limpiar artículos de prueba:
```bash
python manage.py shell -c "from inventario.models import Articulo; Articulo.objects.filter(codigo_barras__startswith='7898').delete(); print('Artículos de prueba eliminados')"
```

---

## 📚 Más Información

- Estrategia completa: `tests/ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md`
- Código de pruebas: `tests/test_carga_masiva_articulos.py`
- Script standalone: `tests/test_carga_standalone.py`
- Locust file: `tests/locustfile_articulos.py`

---

**¿Listo para empezar?** 🎉

```bash
python tests/test_carga_standalone.py
```

**Tiempo estimado**: 5-10 minutos  
**Requerimientos**: Django corriendo, productos en DB  
**Resultado**: Reporte JSON + Resumen en terminal
