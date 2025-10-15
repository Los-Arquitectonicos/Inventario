# Resumen de Cambios - Distribucion Multi-Bodega

## Fecha
Octubre 15, 2025

## Objetivo
Modificar el sistema de pruebas de carga para distribuir articulos entre multiples bodegas y ubicaciones, aumentando significativamente la capacidad total del sistema.

## Cambios Realizados

### 1. Script de Generacion Postman
**Archivo:** `scripts_llenar_db/generar_postman_bodegas_ubicaciones.py`

**Funcionalidad:**
- Genera coleccion Postman para crear infraestructura masiva
- Crea 10 bodegas en diferentes ciudades
- Crea 100 ubicaciones por bodega (1,000 total)
- Capacidad: 1,000,000 articulos por ubicacion
- **Capacidad total: 1,000,000,000 articulos**

**Uso:**
```bash
python generar_postman_bodegas_ubicaciones.py
```

**Output:**
- `postman_bodegas_ubicaciones.json` (1,010 requests)

### 2. Modificacion de Pruebas de Carga
**Archivo:** `tests/locustfile.py`

**Cambios:**
1. Variables globales modificadas:
   ```python
   # ANTES
   UBICACION_ID = int(os.environ.get('UBICACION_ID', '1'))
   BODEGA_ID = int(os.environ.get('BODEGA_ID', '1'))
   
   # DESPUES
   UBICACION_IDS = [1]  # Lista de ubicaciones
   BODEGA_IDS = [1]     # Lista de bodegas
   ```

2. Generador de articulos actualizado:
   ```python
   # ANTES
   'ubicacion_id': UBICACION_ID
   
   # DESPUES
   'ubicacion_id': random.choice(UBICACION_IDS)  # Distribucion aleatoria
   ```

3. Inicializacion mejorada:
   ```python
   # Obtiene TODAS las ubicaciones disponibles (limite: 2000)
   ubicaciones_url = f"{BASE_URL}/api/ubicaciones/?limit=2000"
   UBICACION_IDS = [u['id'] for u in ubicaciones_data['ubicaciones']]
   
   # Detecta bodegas automaticamente
   BODEGA_IDS = list(set(u['bodega_id'] for u in ubicaciones_data['ubicaciones']))
   ```

**Beneficios:**
- Distribucion automatica entre ubicaciones
- Evita saturar una sola ubicacion
- Pruebas mas realistas (multi-bodega)

### 3. Documentacion
**Archivos creados:**

1. `scripts_llenar_db/README_BODEGAS_UBICACIONES.md`
   - Guia completa de uso
   - Instrucciones de Postman
   - Verificacion de creacion
   - Beneficios del sistema distribuido

2. Actualizacion de `tests/README.md`
   - Nueva seccion para preparacion de datos
   - Paso 1: Productos (50 productos)
   - Paso 2: Bodegas y ubicaciones (1,000 ubicaciones)

### 4. Script Django (Alternativo)
**Archivo:** `scripts_llenar_db/crear_bodegas_ubicaciones.py`

**Funcionalidad:**
- Creacion directa via Django ORM
- Util para desarrollo local
- Mismo resultado que Postman

**Uso:**
```bash
python crear_bodegas_ubicaciones.py
```

## Arquitectura Resultante

### Antes
```
1 Bodega
  └── 1 Ubicacion (capacidad: 20,000)
      └── Total: 20,000 articulos
```

### Despues
```
10 Bodegas
  ├── Bodega 1 (Bogota)
  │   └── 100 Ubicaciones (1M c/u)
  ├── Bodega 2 (Medellin)
  │   └── 100 Ubicaciones (1M c/u)
  ├── ...
  └── Bodega 10 (Cucuta)
      └── 100 Ubicaciones (1M c/u)

Total: 1,000 ubicaciones
Capacidad: 1,000,000,000 articulos
```

## Metricas de Distribucion

### Estadisticas Esperadas
- **Ubicaciones por bodega:** 100
- **Articulos por ubicacion (promedio):** Depende de la prueba
  - Baseline (100 articulos): ~0.1 por ubicacion
  - Objective (10,000 articulos): ~10 por ubicacion
  - Max (10,000 articulos): ~10 por ubicacion

### Distribucion Aleatoria
```python
# Cada articulo se asigna a una ubicacion aleatoria
ubicacion_id = random.choice(UBICACION_IDS)
```

**Ventajas:**
- Distribucion uniforme (ley de grandes numeros)
- No hay "hot spots" (ubicaciones saturadas)
- Simula operacion real multi-bodega

## Instrucciones de Uso

### Paso 1: Generar Coleccion
```bash
cd scripts_llenar_db
python generar_postman_bodegas_ubicaciones.py
```

### Paso 2: Ejecutar en Postman
1. Importar `postman_bodegas_ubicaciones.json`
2. Run collection
3. Delay: 50-100ms
4. Tiempo: ~2 minutos

### Paso 3: Verificar
```bash
# Via API
curl http://[ALB_URL]/inventario/api/ubicaciones/?limit=2000 | jq '.ubicaciones | length'

# Debe retornar: 1000
```

### Paso 4: Ejecutar Pruebas
```bash
./tests/run_load_tests.sh objective
```

**Output esperado:**
```
[INFO] Obteniendo IDs del servidor...
[OK] 50 productos disponibles
[OK] 1000 ubicaciones disponibles
[OK] 10 bodegas disponibles
```

## Resultados Esperados

### Distribucion de Articulos (Prueba Objective: 10,000 articulos)
- **Articulos por ubicacion (promedio):** 10
- **Articulos por ubicacion (min):** ~5
- **Articulos por ubicacion (max):** ~15
- **Articulos por bodega (promedio):** 1,000

### Capacidad Utilizada
- **Prueba Baseline (100 articulos):** 0.00001% de capacidad
- **Prueba Objective (10,000 articulos):** 0.001% de capacidad
- **Capacidad disponible restante:** 999,990,000 articulos

## Archivos Modificados

```
scripts_llenar_db/
├── generar_postman_bodegas_ubicaciones.py  [NUEVO]
├── crear_bodegas_ubicaciones.py            [NUEVO]
├── README_BODEGAS_UBICACIONES.md           [NUEVO]
└── postman_bodegas_ubicaciones.json        [GENERADO]

tests/
├── locustfile.py                           [MODIFICADO]
└── README.md                               [MODIFICADO]
```

## Compatibilidad

### Backward Compatible
✅ Las pruebas siguen funcionando con 1 ubicacion
✅ Si solo hay 1 ubicacion, `random.choice([1])` = 1
✅ No requiere cambios en el backend

### Forward Compatible
✅ Detecta automaticamente todas las ubicaciones
✅ Escala de 1 a 1,000+ ubicaciones sin cambios
✅ Funciona con cualquier numero de bodegas

## Testing

### Validar Distribucion
Despues de ejecutar una prueba, verificar distribucion:

```python
from inventario.models import Articulo
from collections import Counter

# Contar articulos por ubicacion
articulos = Articulo.objects.all()
distribucion = Counter(a.ubicacion_id for a in articulos)

print(f"Ubicaciones con articulos: {len(distribucion)}")
print(f"Articulos por ubicacion (min): {min(distribucion.values())}")
print(f"Articulos por ubicacion (max): {max(distribucion.values())}")
print(f"Articulos por ubicacion (avg): {sum(distribucion.values()) / len(distribucion)}")
```

## Conclusiones

### Beneficios Logrados
1. **Escalabilidad:** Capacidad aumentada 50,000x (20K → 1,000M)
2. **Realismo:** Simula operacion multi-bodega real
3. **Distribucion:** Evita saturacion de ubicaciones
4. **Flexibilidad:** Funciona con 1 o 1,000 ubicaciones
5. **Automatico:** No requiere configuracion manual

### Proximos Pasos
1. Ejecutar coleccion Postman para crear bodegas
2. Ejecutar pruebas de carga
3. Validar distribucion uniforme
4. Analizar metricas por bodega (opcional)
