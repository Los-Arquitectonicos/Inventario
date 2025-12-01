from django.contrib import admin

from inventario.models import *
# Register your models here.
admin.site.register(Bodega)
admin.site.register(UbicacionBodega)
admin.site.register(Producto)
admin.site.register(Articulo)
admin.site.register(Cliente)
admin.site.register(Usuario)
admin.site.register(Cotizacion)
admin.site.register(Pedido)
admin.site.register(PedidoProducto)
admin.site.register(Factura)


