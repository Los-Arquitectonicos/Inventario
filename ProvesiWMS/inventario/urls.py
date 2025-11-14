from django.urls import path
from . import views, auth_views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'inventario'

urlpatterns = [
    # ===========================
    # ENDPOINTS DE AUTENTICACIÓN
    # ===========================
    
    # Autenticación JWT
    path("auth/login/", auth_views.login_api, name="login_api"),
    path("auth/logout/", auth_views.logout_api, name="logout_api"), 
    path("auth/profile/", auth_views.user_profile, name="user_profile"),
    path("auth/verify/", auth_views.verify_token, name="verify_token"),
    path("auth/change-password/", auth_views.change_password, name="change_password"),
    
    # Tokens JWT (usando vistas de rest_framework_simplejwt)
    path("auth/token/", auth_views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # ===========================
    # VISTAS PRINCIPALES  
    # ===========================
    
    # Vista principal
    path("", views.index, name="index"),
    
    # URLs de Productos
    path("productos/", views.ProductoListView.as_view(), name="productos_lista"),
    path("productos/<int:pk>/", views.ProductoDetailView.as_view(), name="producto_detalle"),
    path("productos/sin-stock/", views.productos_sin_stock, name="productos_sin_stock"),
    path("productos/crear/", views.crear_producto, name="crear_producto"),
    path("productos/<int:producto_id>/actualizar/", views.actualizar_producto, name="actualizar_producto"),
    path("productos/<int:producto_id>/eliminar/", views.eliminar_producto, name="eliminar_producto"), # type: ignore
    
    # URLs de Bodegas
    path("bodegas/", views.BodegaListView.as_view(), name="bodegas_lista"),
    path("bodegas/<int:pk>/", views.BodegaDetailView.as_view(), name="bodega_detalle"),
    path("bodegas/crear/", views.crear_bodega, name="crear_bodega"),
    path("bodegas/<int:bodega_id>/actualizar/", views.actualizar_bodega, name="actualizar_bodega"), # type: ignore
    path("bodegas/<int:bodega_id>/eliminar/", views.eliminar_bodega, name="eliminar_bodega"), # type: ignore
    
    # URLs de Ubicaciones de Bodega
    path("ubicaciones/crear/", views.crear_ubicacion_bodega, name="crear_ubicacion_bodega"),
    path("ubicaciones/crear_batch/", views.crear_ubicaciones_batch, name="crear_ubicaciones_batch"),
    path("ubicaciones/<int:ubicacion_id>/actualizar/", views.actualizar_ubicacion_bodega, name="actualizar_ubicacion_bodega"), # type: ignore
    path("ubicaciones/<int:ubicacion_id>/eliminar/", views.eliminar_ubicacion_bodega, name="eliminar_ubicacion_bodega"), # type: ignore
    
    # URLs de Pedidos
    path("pedidos/", views.PedidoListView.as_view(), name="pedidos_lista"),
    path("pedidos/<int:pk>/", views.PedidoDetailView.as_view(), name="pedido_detalle"),
    path("pedidos/crear/", views.crear_pedido, name="crear_pedido"),
    path("pedidos/<int:pedido_id>/actualizar-estado/", views.actualizar_estado_pedido, name="actualizar_estado_pedido"),
    
    # URLs de Clientes
    path("clientes/", views.ClienteListView.as_view(), name="clientes_lista"),
    path("clientes/<int:pk>/", views.ClienteDetailView.as_view(), name="cliente_detalle"),
    path("clientes/crear/", views.crear_cliente, name="crear_cliente"),
    path("clientes/<int:cliente_id>/actualizar/", views.actualizar_cliente, name="actualizar_cliente"), # type: ignore
    path("clientes/<int:cliente_id>/eliminar/", views.eliminar_cliente, name="eliminar_cliente"), # type: ignore
    
    # URLs de Artículos
    path("articulos/crear/", views.crear_articulo, name="crear_articulo"),
    path("articulos/crear_batch/", views.crear_articulos_batch, name="crear_articulos_batch"),
    path("articulos/<int:articulo_id>/actualizar/", views.actualizar_articulo, name="actualizar_articulo"), # type: ignore
    path("articulos/<int:articulo_id>/eliminar/", views.eliminar_articulo, name="eliminar_articulo"), # type: ignore
    
    # URLs de Usuarios
    path("usuarios/crear/", views.crear_usuario, name="crear_usuario"),
    path("usuarios/<int:usuario_id>/actualizar/", views.actualizar_usuario, name="actualizar_usuario"), # type: ignore
    path("usuarios/<int:usuario_id>/eliminar/", views.eliminar_usuario, name="eliminar_usuario"), # type: ignore
    
    # URLs de Reportes
    path("reportes/inventario/", views.reporte_inventario, name="reporte_inventario"),
    path("reportes/ventas/", views.reporte_ventas, name="reporte_ventas"),
    
    # URLs de API
    path("api/productos/stock/", views.api_productos_stock, name="api_productos_stock"),
    path("api/productos/buscar/", views.api_buscar_productos, name="api_buscar_productos"),
    path("api/pedidos/<int:pedido_id>/total/", views.api_pedido_total, name="api_pedido_total"),
    path("api/estadisticas/completas/", views.api_estadisticas_completas, name="api_estadisticas_completas"),
    path("api/articulos/", views.api_listar_articulos, name="api_listar_articulos"),
    
    # APIs para listar todos los modelos
    path("api/productos/", views.api_listar_productos, name="api_listar_productos"),
    path("api/bodegas/", views.api_listar_bodegas, name="api_listar_bodegas"),
    path("api/ubicaciones/", views.api_listar_ubicaciones, name="api_listar_ubicaciones"),
    path("api/clientes/", views.api_listar_clientes, name="api_listar_clientes"),
    path("api/usuarios/", views.api_listar_usuarios, name="api_listar_usuarios"),
    path("api/pedidos/", views.api_listar_pedidos, name="api_listar_pedidos"),
    path("api/pedidos/<int:pedido_id>/", views.api_actualizar_pedido, name="api_actualizar_pedido"),
    path("api/cotizaciones/", views.api_listar_cotizaciones, name="api_listar_cotizaciones"),
    path("api/facturas/", views.api_listar_facturas, name="api_listar_facturas"),
    
    # APIs de eliminación masiva
    path("api/articulos/eliminar_todos/", views.eliminar_todos_articulos, name="eliminar_todos_articulos"),
    path("api/ubicaciones/eliminar_todas/", views.eliminar_todas_ubicaciones, name="eliminar_todas_ubicaciones"),
    path("api/bodegas/eliminar_todas/", views.eliminar_todas_bodegas, name="eliminar_todas_bodegas"),
    path("api/productos/eliminar_todos/", views.eliminar_todos_productos, name="eliminar_todos_productos"),
]