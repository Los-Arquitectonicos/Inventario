# 🧪 Tests - Carga Masiva de Artículos

## 📋 Contenido del Directorio

Este directorio contiene la suite completa de pruebas de carga masiva para validar el requerimiento arquitecturalmente significativo del sistema de inventario.

---

## 🎯 Objetivo

Validar que el sistema puede:
- ✅ Escalar de **100 req/min** a **2,000 req/min**
- ✅ Procesar **10,000 artículos** en menos de **5 minutos**
- ✅ Mantener **integridad de datos** (>95%)
- ✅ Soportar carga sin **degradación**

---

## 📁 Archivos

### 🚀 Scripts Ejecutables

| Archivo | Descripción | Comando |
|---------|-------------|---------|
| `test_carga_standalone.py` | ⭐ **Script standalone con menú interactivo** | `python tests/test_carga_standalone.py` |
| `test_carga_masiva_articulos.py` | Tests de Django (integración) | `python manage.py test tests.test_carga_masiva_articulos` |
| `locustfile_articulos.py` | Tests de performance con Locust | `locust -f tests/locustfile_articulos.py` |

### 📖 Documentación

| Archivo | Descripción |
|---------|-------------|
| `INDEX.md` | 📑 Índice general - **EMPIEZA AQUÍ** |
| `RESUMEN_EJECUTIVO.md` | 📊 Resumen ejecutivo y estrategia |
| `README_PRUEBAS_RAPIDAS.md` | ⚡ Guía de inicio rápido |
| `ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md` | 📚 Documentación técnica completa |
| `VISUAL_SUMMARY.md` | 🎨 Resumen visual con gráficos |
| `README.md` | 📄 Este archivo |

---

## ⚡ Inicio Rápido (30 segundos)

```bash
# Terminal 1: Iniciar servidor
python manage.py runserver

# Terminal 2: Ejecutar pruebas
python tests/test_carga_standalone.py
# Seleccionar: Opción 3 (Test Objetivo Principal)
```

---

## 🧪 Tests Disponibles

### 1. Test Baseline (100 artículos)
- Duración: ~30 segundos
- Objetivo: Línea base de rendimiento

### 2. Test Concurrente (1,000 artículos)
- Duración: ~2 minutos
- Objetivo: Validar procesamiento paralelo

### 3. Test Objetivo Principal (10,000 artículos) ⭐
- Duración: < 5 minutos
- Objetivo: **VALIDAR REQUERIMIENTO COMPLETO**

### 4. Test Escalabilidad (Incremental)
- Duración: ~10 minutos
- Objetivo: Probar escalamiento de 100 a 2,000 req/min

### 5. Test Errores Parciales
- Duración: ~1 minuto
- Objetivo: Validar resiliencia

---

## 📊 Métricas Validadas

```
✅ Throughput (req/min)
✅ Latencia (P50, P95, P99)
✅ Tasa de éxito (%)
✅ Tiempo de procesamiento (segundos)
✅ Consistencia en DB (%)
```

---

## 🎯 Criterios de Éxito

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Tiempo 10k artículos | ≤ 300s | ✅ |
| Throughput | 100-2,000 req/min | ✅ |
| Tasa de éxito | ≥ 95% | ✅ |
| Integridad DB | ≥ 95% | ✅ |

---

## 🛠️ Herramientas

### Para Usuarios No Técnicos
👉 **Usar**: `test_carga_standalone.py`
- Menú interactivo
- Colores y progreso
- Fácil de usar

### Para Automatización/CI
👉 **Usar**: `test_carga_masiva_articulos.py`
- Tests unitarios
- Integrado con Django
- Asserts automáticos

### Para Análisis Avanzado
👉 **Usar**: `locustfile_articulos.py`
- Interfaz web
- Gráficos en tiempo real
- Reportes HTML

---

## 📈 Reportes Generados

```
reporte_carga_masiva.json    # Reporte detallado
reporte_locust.html          # Reporte Locust (si se usa)
```

---

## 🔗 Enlaces Útiles

- [INDEX.md](INDEX.md) - Índice completo
- [RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md) - Estrategia completa
- [README_PRUEBAS_RAPIDAS.md](README_PRUEBAS_RAPIDAS.md) - Comandos rápidos

---

## 💡 Recomendaciones

1. **Primera vez**: Lee `INDEX.md` completo
2. **Rápido**: Usa `README_PRUEBAS_RAPIDAS.md`
3. **Detalle**: Consulta `ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md`
4. **Visual**: Revisa `VISUAL_SUMMARY.md`

---

## 🚀 Comando Más Rápido

```bash
python tests/test_carga_standalone.py <<< "3"
```

Este comando ejecuta directamente el test objetivo de 10,000 artículos.

---

## ⚠️ Prerequisitos

- [ ] Servidor Django corriendo
- [ ] Productos en DB (>50)
- [ ] Ubicaciones en DB (>1)
- [ ] `pip install requests`

---

## 📞 Troubleshooting

### "No se puede conectar al servidor"
```bash
# Verificar servidor
curl http://127.0.0.1:8000/inventario/
```

### "ModuleNotFoundError: requests"
```bash
pip install requests
```

### Throughput muy bajo
```bash
# Aumentar workers en el script
# Línea ~260 de test_carga_standalone.py
workers = 70  # Aumentar de 50 a 70
```

---

## 📝 Notas

- Los tests crean artículos con códigos que empiezan con `7898`
- Puedes limpiar los artículos de prueba después
- Los tests NO afectan los datos de producción
- Se recomienda ejecutar en ambiente de desarrollo

---

## 🎓 Flujo Recomendado

```
1. Lee INDEX.md (5 min)
   ↓
2. Ejecuta test_carga_standalone.py (10 min)
   ↓
3. Revisa reporte_carga_masiva.json (5 min)
   ↓
4. Si necesitas detalles: ESTRATEGIA_PRUEBAS_CARGA_MASIVA.md
```

---

## ✅ Checklist

- [ ] Leí la documentación
- [ ] Servidor Django corriendo
- [ ] Ejecuté al menos un test
- [ ] Revisé los resultados
- [ ] Compartí con el equipo

---

**¿Listo para empezar?** 🚀

```bash
python tests/test_carga_standalone.py
```

---

**Última actualización**: 2025-10-13  
**Versión**: 1.0  
**Estado**: ✅ Listo para usar
