# 📚 Índice de Pruebas de Carga Masiva

## 🎯 Objetivo
Validar el requerimiento arquitecturalmente significativo de escalar el procesamiento de artículos desde **100 req/min hasta 2,000 req/min**, procesando **10,000 registros en menos de 5 minutos**.

---

## 📁 Archivos de Prueba

### 🔧 Scripts de Prueba (Ejecutables)

| Archivo | Tipo | Descripción | Ejecución |
|---------|------|-------------|-----------|
| **test_carga_standalone.py** | Python Script | ⭐ **RECOMENDADO**: Script independiente con menú interactivo | `python tests/test_carga_standalone.py` |
| **test_carga_masiva_articulos.py** | Django Tests | Tests unitarios integrados con Django | `python manage.py test tests.test_carga_masiva_articulos` |
| **locustfile_articulos.py** | Locust | Pruebas de carga con interfaz web | `locust -f tests/locustfile_articulos.py` |

### 📖 Documentación

| Archivo | Descripción |
|---------|-------------|
| **RESUMEN_EJECUTIVO.md** | ⭐ Resumen ejecutivo y respuesta a la pregunta principal |
| **ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md** | Documentación completa de la estrategia |
| **README_PRUEBAS_RAPIDAS.md** | Guía rápida de inicio |
| **INDEX.md** | Este archivo - índice general |

---

## 🚀 Inicio Rápido (2 minutos)

### Paso 1: Iniciar Servidor
```bash
cd ProvesiWMS
python manage.py runserver
```

### Paso 2: Ejecutar Pruebas (en otra terminal)
```bash
cd ProvesiWMS
python tests/test_carga_standalone.py
```

### Paso 3: Seleccionar Test
```
Opción 3: Test Objetivo Principal (10,000 artículos)
```

---

## 🧪 Tests Disponibles

### Test 1: Baseline
- **Cantidad**: 100 artículos
- **Modo**: Secuencial
- **Duración**: ~30 segundos
- **Valida**: Rendimiento base

### Test 2: Concurrencia
- **Cantidad**: 1,000 artículos
- **Modo**: 10 workers concurrentes
- **Duración**: ~2 minutos
- **Valida**: Procesamiento paralelo

### Test 3: Objetivo Principal ⭐
- **Cantidad**: 10,000 artículos
- **Modo**: 50 workers concurrentes
- **Duración objetivo**: < 5 minutos
- **Valida**: REQUERIMIENTO COMPLETO

### Test 4: Escalabilidad
- **Cargas**: 100 → 500 → 1,000 → 2,000
- **Modo**: Workers incrementales
- **Duración**: ~10 minutos
- **Valida**: Escalamiento de 100 a 2,000 req/min

### Test 5: Errores Parciales
- **Cantidad**: 100 artículos (90 válidos + 10 duplicados)
- **Duración**: ~1 minuto
- **Valida**: Resiliencia y manejo de errores

---

## 📊 Criterios de Éxito

```
✅ Tiempo total ≤ 300 segundos (5 minutos)
✅ Throughput entre 100-2,000 req/min
✅ Tasa de éxito ≥ 95%
✅ Consistencia en DB ≥ 95%
✅ Sin degradación de servicio
```

---

## 🛠️ Herramientas por Escenario

### Para QA Manual
👉 **Usar**: `test_carga_standalone.py`
- Menú interactivo
- Colores y progreso visual
- Más fácil de usar

### Para CI/CD y Automatización
👉 **Usar**: `test_carga_masiva_articulos.py`
- Tests unitarios estándar
- Integración con Django
- Assert automáticos

### Para Análisis Detallado
👉 **Usar**: `locustfile_articulos.py`
- Interfaz web con gráficos
- Reportes HTML
- Métricas avanzadas

---

## 📈 Reportes Generados

Después de ejecutar las pruebas:

```
ProvesiWMS/
├── reporte_carga_masiva.json    # Script standalone
├── reporte_locust.html          # Locust (si se usa)
└── reporte_locust.csv           # Locust raw data
```

---

## 🎓 Flujo Recomendado

```
1. Leer: RESUMEN_EJECUTIVO.md
   ↓
2. Seguir: README_PRUEBAS_RAPIDAS.md
   ↓
3. Ejecutar: test_carga_standalone.py (Opción 3)
   ↓
4. Analizar: reporte_carga_masiva.json
   ↓
5. Si necesita más detalle: ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md
```

---

## ⚡ Comandos Esenciales

```bash
# Verificar servidor
curl http://127.0.0.1:8000/inventario/

# Ejecutar test objetivo
python tests/test_carga_standalone.py <<< "3"

# Ver reporte
cat reporte_carga_masiva.json | python -m json.tool

# Limpiar artículos de prueba
python manage.py shell -c "from inventario.models import Articulo; Articulo.objects.filter(codigo_barras__startswith='7898').delete()"
```

---

## 📞 Preguntas Frecuentes

### ¿Cuál herramienta usar?
**R**: Para empezar, usa `test_carga_standalone.py` - es el más fácil.

### ¿Cuánto tiempo toma?
**R**: El test principal toma ~5-10 minutos.

### ¿Necesito instalar algo?
**R**: Solo `pip install requests` para el script standalone.

### ¿Afecta la base de datos?
**R**: Crea artículos de prueba. Puedes limpiarlos después.

### ¿Cómo sé si pasó la prueba?
**R**: Busca "✅ EXITOSO" en el resumen final.

---

## 🔗 Enlaces Rápidos

| Documento | Para qué sirve |
|-----------|----------------|
| [RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md) | Entender la estrategia completa |
| [README_PRUEBAS_RAPIDAS.md](README_PRUEBAS_RAPIDAS.md) | Empezar rápido |
| [ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md](ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md) | Documentación técnica detallada |

---

## ✅ Checklist Antes de Empezar

- [ ] Servidor Django corriendo
- [ ] Base de datos tiene productos (>50)
- [ ] Python 3.9+ instalado
- [ ] `requests` instalado (`pip install requests`)
- [ ] Terminal lista para ejecutar comandos

---

## 🎯 Siguiente Paso

```bash
python tests/test_carga_standalone.py
```

**¡Buena suerte con las pruebas!** 🚀

---

**Última actualización**: 2025-10-13  
**Autor**: Sistema de Pruebas ProvesiWMS  
**Versión**: 1.0
