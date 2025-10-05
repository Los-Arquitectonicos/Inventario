"""
cargar_demo_50k
---------------
Un solo comando para preparar y cargar 50.000 artículos de prueba.

Flujo:
1) (por defecto) ejecuta 'sembrar_catalogo' para garantizar productos/bodegas/zonas.
2) genera un CSV temporal con el formato esperado (encabezados EXACTOS).
3) llama internamente a 'cargar_csv_local' con batch-size configurable.
4) imprime resumen y tiempo total.

Uso:
  python manage.py cargar_demo_50k
Opcionales:
  --objetivo 60000         # por defecto 50000
  --batch-size 2000        # por defecto 2000
  --sin-sembrar            # si NO quieres ejecutar sembrar_catalogo
"""

import csv
import os
import time
import tempfile
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

from inventario.models import Articulo

class Command(BaseCommand):
    help = "Ejecuta una demo de carga masiva (50k por defecto) en una sola vez."

    def add_arguments(self, parser):
        parser.add_argument("--objetivo", type=int, default=50000,
                            help="Cantidad total de artículos a crear (default 50000).")
        parser.add_argument("--batch-size", type=int, default=2000,
                            help="Tamaño del lote para bulk_create (default 2000).")
        parser.add_argument("--sin-sembrar", action="store_true",
                            help="No ejecutar sembrar_catalogo antes de la carga.")

    def handle(self, *args, **opts):
        objetivo = max(1, int(opts["objetivo"]))
        batch_size = max(1, int(opts["batch_size"]))
        hacer_siembra = not opts["sin_sembrar"]

        t0 = time.time()

        # 1) Sembrar catálogo (productos/bodegas/zonas)
        if hacer_siembra:
            self.stdout.write(self.style.NOTICE("Sembrando catálogo mínimo..."))
            call_command("sembrar_catalogo")  # debe existir el comando

        # 2) Generar CSV temporal con encabezados EXACTOS
        tmpdir = tempfile.gettempdir()
        ruta_csv = os.path.join(tmpdir, f"carga_{objetivo}.csv")
        self.stdout.write(self.style.NOTICE(f"Generando CSV temporal: {ruta_csv}"))

        zonas = [f"Z-{i:03d}" for i in range(1, 31)]  # Z-001 .. Z-030
        total = 0
        sku_i = 1
        with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "sku","codigo_bodega","codigo_zona","cantidad",
                "lote","precio_costo_real","fecha_fabricacion","fecha_vencimiento","numero_serie"
            ])
            while total < objetivo:
                cant = min(50, objetivo - total)  # 50 por fila para acelerar
                w.writerow([
                    f"SKU-{sku_i:05d}",             # sku existente (sembrar_catalogo crea 1000+)
                    "BOD-NORTE",                    # bodega creada por el seeder
                    zonas[(sku_i - 1) % 30],        # zona válida
                    cant,
                    "LOTE-A",
                    "12.50",
                    "2025-01-01",
                    "2026-01-01",
                    ""                              # numero_serie vacío (no serializados)
                ])
                total += cant
                sku_i += 1

        self.stdout.write(self.style.SUCCESS(f"CSV generado con {total} unidades."))

        # 3) Llamar a tu loader existente (cargar_csv_local)
        self.stdout.write(self.style.NOTICE(
            f"Cargando artículos con batch_size={batch_size}..."
        ))
        call_command("cargar_csv_local", ruta_csv, batch_size=batch_size)

        # 4) Resumen final
        t1 = time.time()
        conteo = Articulo.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"¡Listo! Artículos totales en BD = {conteo}. "
            f"Tiempo total = {t1 - t0:.2f}s (incluye siembra + CSV + carga)."
        ))
