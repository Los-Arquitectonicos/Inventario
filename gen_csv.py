import csv, os

# Ruta donde se guardará el CSV
os.makedirs(r"C:\tmp", exist_ok=True)
path = r"C:\tmp\carga.csv"

with open(path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    # Encabezados EXACTOS que espera el comando
    w.writerow([
        "sku","codigo_bodega","codigo_zona","cantidad",
        "lote","precio_costo_real","fecha_fabricacion","fecha_vencimiento","numero_serie"
    ])

    # Generamos 10.000 unidades (200 filas x 50 unidades, aprox)
    zonas = [f"Z-{i:03d}" for i in range(1, 31)]
    total = 0
    sku_i = 1
    while total < 10000:
        cant = min(50, 10000 - total)
        w.writerow([
            f"SKU-{sku_i:05d}",       # SKU
            "BOD-NORTE",              # bodega (la crea el 'sembrar_catalogo')
            zonas[(sku_i - 1) % 30],  # zona válida para esa bodega
            cant,                     # cantidad
            "LOTE-A",                 # lote
            "12.50",                  # precio_costo_real
            "2025-01-01",             # fecha_fabricacion
            "2026-01-01",             # fecha_vencimiento
            ""                        # numero_serie (vacío porque no serializados)
        ])
        total += cant
        sku_i += 1

print("CSV listo en:", path)
