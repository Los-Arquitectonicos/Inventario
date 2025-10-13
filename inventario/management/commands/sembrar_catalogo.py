from django.core.management.base import BaseCommand
from decimal import Decimal
from inventario.models import Producto, Bodega, ZonaBodega

class Command(BaseCommand):
    help = "Crea productos, bodegas y zonas mínimas para pruebas"

    def handle(self, *args, **kwargs):
        nuevos = []
        for i in range(1, 1001):
            sku = f"SKU-{i:05d}"
            if not Producto.objects.filter(sku=sku).exists():
                nuevos.append(Producto(
                    sku=sku, nombre=f"Producto {i}",
                    precio_costo=Decimal("10.00"), precio_venta=Decimal("15.00"),
                    activo=True, es_serializado=False, requiere_numero_serie=False
                ))
        if nuevos:
            Producto.objects.bulk_create(nuevos, batch_size=1000)

        b1, _ = Bodega.objects.get_or_create(codigo="BOD-NORTE",
                defaults=dict(nombre="Bodega Norte", direccion="Norte", ciudad="Bogotá"))
        b2, _ = Bodega.objects.get_or_create(codigo="BOD-CENTRO",
                defaults=dict(nombre="Bodega Centro", direccion="Centro", ciudad="Bogotá"))
        b3, _ = Bodega.objects.get_or_create(codigo="BOD-SUR",
                defaults=dict(nombre="Bodega Sur", direccion="Sur", ciudad="Bogotá"))
        for b in (b1,b2,b3):
            faltan = []
            for i in range(1,31):
                cod = f"Z-{i:03d}"
                if not b.zonas.filter(codigo=cod).exists():
                    faltan.append(ZonaBodega(bodega=b, codigo=cod, nombre=f"Zona {cod}"))
            if faltan:
                ZonaBodega.objects.bulk_create(faltan, batch_size=500)

        self.stdout.write(self.style.SUCCESS("Catálogo mínimo listo."))
