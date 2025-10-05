"""
Comando local para cargar un CSV y crear Artículos en lotes (bulk_create).
No usa AWS. Actualiza la tabla CargaMasiva para dejar traza.

Uso:
  python manage.py cargar_csv_local "C:\tmp\carga.csv" [--id-carga 123] [--batch-size 2000]

El CSV debe tener exactamente estos encabezados:
  sku,codigo_bodega,codigo_zona,cantidad,lote,precio_costo_real,fecha_fabricacion,fecha_vencimiento,numero_serie
"""

import csv
import os
import uuid
import time
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from inventario.models import (
    CargaMasiva,
    Producto,
    Bodega,
    ZonaBodega,
    Articulo,
)


class Command(BaseCommand):
    help = "Carga un CSV local y crea Artículos en lotes. Actualiza CargaMasiva."

    def add_arguments(self, parser):
        parser.add_argument("ruta_csv", type=str, help="Ruta del archivo CSV")
        parser.add_argument(
            "--id-carga",
            type=int,
            default=None,
            help="Id de CargaMasiva existente (opcional). Si no se envía, se crea uno nuevo.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=2000,
            help="Tamaño del lote para bulk_create (por defecto 2000).",
        )

    # ------------------- utilidades -------------------

    def _leer_csv(self, ruta_csv: str) -> list[dict]:
        if not os.path.isfile(ruta_csv):
            raise CommandError(f"No existe el archivo: {ruta_csv}")

        with open(ruta_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            esperadas = {
                "sku",
                "codigo_bodega",
                "codigo_zona",
                "cantidad",
                "lote",
                "precio_costo_real",
                "fecha_fabricacion",
                "fecha_vencimiento",
                "numero_serie",
            }
            if reader.fieldnames is None:
                raise CommandError("El CSV no tiene encabezados.")

            cols = set([c.strip() for c in reader.fieldnames])
            if not esperadas.issubset(cols):
                faltantes = sorted(list(esperadas - cols))
                raise CommandError(
                    f"Encabezados faltantes: {faltantes}. "
                    f"Se esperan EXACTAMENTE: {sorted(esperadas)}"
                )

            filas = []
            for r in reader:
                # normalizo espacios por si acaso
                filas.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()})
        return filas

    # ------------------- handle -------------------

    def handle(self, *args, **opts):
        ruta_csv: str = opts["ruta_csv"]
        id_carga = opts["id_carga"]
        batch_size = max(1, int(opts["batch_size"]))

        # 1) prepara/crea registro de CargaMasiva
        if id_carga is None:
            carga = CargaMasiva.objects.create(
                clave_s3=ruta_csv,  # guardo la ruta local aquí
                estado="PROCESANDO",
                inicio=timezone.now(),
            )
            id_carga = carga.id
        else:
            # si vino un id, lo marco en PROCESANDO
            CargaMasiva.objects.filter(id=id_carga).update(
                clave_s3=ruta_csv, estado="PROCESANDO", inicio=timezone.now(), error=None
            )
            try:
                carga = CargaMasiva.objects.get(id=id_carga)
            except CargaMasiva.DoesNotExist:
                raise CommandError(f"No existe CargaMasiva con id={id_carga}")

        t0 = time.time()

        # 2) leo CSV
        filas = self._leer_csv(ruta_csv)

        # 3) precargo catálogos para minimizar queries
        skus = {r["sku"] for r in filas if r.get("sku")}
        cod_bodegas = {r["codigo_bodega"] for r in filas if r.get("codigo_bodega")}
        cod_zonas = {r["codigo_zona"] for r in filas if r.get("codigo_zona")}

        productos = {
            p.sku: (p.id, p.es_serializado, p.requiere_numero_serie)
            for p in Producto.objects.filter(sku__in=skus)
        }
        bodegas = {b.codigo: b for b in Bodega.objects.filter(codigo__in=cod_bodegas)}
        zonas_qs = ZonaBodega.objects.select_related("bodega").filter(
            codigo__in=cod_zonas, bodega__codigo__in=cod_bodegas
        )
        zonas = {(z.bodega.codigo, z.codigo): z for z in zonas_qs}

        faltan_sku = sorted(list(skus - set(productos.keys())))
        if faltan_sku:
            raise CommandError(f"SKU no encontrados (ejemplos): {faltan_sku[:5]} ...")

        faltan_bod = sorted(list(cod_bodegas - set(bodegas.keys())))
        if faltan_bod:
            raise CommandError(f"Bodegas no encontradas (ejemplos): {faltan_bod[:5]} ...")

        # validación zonas por combinación bodega+zona al momento de iterar
        # (así indicamos exactamente cuál falta)

        # 4) inserción por lotes
        batch: list[Articulo] = []
        creados = 0

        try:
            with transaction.atomic():
                for idx, r in enumerate(filas, start=1):
                    sku = r["sku"]
                    codigo_bodega = r["codigo_bodega"]
                    codigo_zona = r["codigo_zona"]
                    cantidad_txt = r.get("cantidad") or "0"
                    lote = r.get("lote") or None
                    precio_txt = (r.get("precio_costo_real") or "").strip()
                    f_fab = r.get("fecha_fabricacion") or None
                    f_ven = r.get("fecha_vencimiento") or None
                    n_serie = (r.get("numero_serie") or None)

                    try:
                        cantidad = int(cantidad_txt)
                    except ValueError:
                        raise CommandError(f"Fila {idx}: 'cantidad' inválida: {cantidad_txt}")

                    precio_costo_real = None
                    if precio_txt:
                        try:
                            precio_costo_real = Decimal(precio_txt)
                        except (InvalidOperation, ValueError):
                            raise CommandError(f"Fila {idx}: 'precio_costo_real' inválido: {precio_txt}")

                    prod_id, es_serial, req_serie = productos[sku]
                    bodega = bodegas[codigo_bodega]
                    zona = zonas.get((codigo_bodega, codigo_zona))
                    if not zona:
                        raise CommandError(
                            f"Fila {idx}: Zona inexistente para bodega={codigo_bodega}, zona={codigo_zona}"
                        )

                    # Caso producto serializado/requiere número de serie: 1 fila = 1 artículo
                    if es_serial or req_serie:
                        if not n_serie:
                            raise CommandError(
                                f"Fila {idx}: producto {sku} es serializado o requiere número de serie."
                            )
                        codigo_interno = f"ART-{sku}-{id_carga}-{n_serie}"
                        batch.append(
                            Articulo(
                                codigo_interno=codigo_interno,
                                producto_id=prod_id,
                                bodega=bodega,
                                zona=zona,
                                numero_serie=n_serie,
                                lote=lote,
                                precio_costo_real=precio_costo_real,
                                fecha_fabricacion=f_fab,
                                fecha_vencimiento=f_ven,
                                estado="disponible",
                            )
                        )
                        if len(batch) >= batch_size:
                            Articulo.objects.bulk_create(batch, batch_size=batch_size)
                            creados += len(batch)
                            batch.clear()
                    else:
                        # Caso no serializado: se crean 'cantidad' artículos idénticos
                        unidades = max(0, cantidad)
                        for _ in range(unidades):
                            codigo_interno = f"ART-{sku}-{id_carga}-{uuid.uuid4().hex[:8].upper()}"
                            batch.append(
                                Articulo(
                                    codigo_interno=codigo_interno,
                                    producto_id=prod_id,
                                    bodega=bodega,
                                    zona=zona,
                                    lote=lote,
                                    precio_costo_real=precio_costo_real,
                                    fecha_fabricacion=f_fab,
                                    fecha_vencimiento=f_ven,
                                    estado="disponible",
                                )
                            )
                            if len(batch) >= batch_size:
                                Articulo.objects.bulk_create(batch, batch_size=batch_size)
                                creados += len(batch)
                                batch.clear()

                if batch:
                    Articulo.objects.bulk_create(batch, batch_size=batch_size)
                    creados += len(batch)

        except Exception as e:
            # registro de error en CargaMasiva
            CargaMasiva.objects.filter(id=id_carga).update(
                estado="FALLA", error=str(e), fin=timezone.now(), filas=len(filas)
            )
            raise

        # 5) fin OK
        CargaMasiva.objects.filter(id=id_carga).update(
            estado="OK", fin=timezone.now(), filas=len(filas)
        )

        t1 = time.time()
        self.stdout.write(
            self.style.SUCCESS(
                f"OK: idCarga={id_carga}, filas_csv={len(filas)}, articulos_creados={creados}, "
                f"tiempo={t1 - t0:.2f}s, batch_size={batch_size}"
            )
        )
