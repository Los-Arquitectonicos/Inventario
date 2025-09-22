"""
URL configuration for inventario project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import productos, bodegas, articulos, movimientos

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Product endpoints
    path('api/productos/', productos.productos_list, name='productos_list'),
    path('api/productos/<int:producto_id>/', productos.producto_detail, name='producto_detail'),
    path('api/productos/<int:producto_id>/articulos/', productos.producto_articulos, name='producto_articulos'),
    path('api/productos/crear/', productos.crear_producto, name='crear_producto'),
    
    # Warehouse endpoints
    path('api/bodegas/', bodegas.bodegas_list, name='bodegas_list'),
    path('api/bodegas/<int:bodega_id>/inventario/', bodegas.bodega_inventario, name='bodega_inventario'),
    
    # Article endpoints
    path('api/articulos/agregar/', articulos.agregar_articulo, name='agregar_articulo'),
    path('api/articulos/<int:articulo_id>/estado/', articulos.actualizar_articulo_estado, name='actualizar_articulo_estado'),
    
    # Movement endpoints
    path('api/articulos/<int:articulo_id>/movimientos/', movimientos.movimientos_articulo, name='movimientos_articulo'),
]
