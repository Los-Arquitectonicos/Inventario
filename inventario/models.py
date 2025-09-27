from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Categorías"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Proveedores"


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True)
    
 
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    peso = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Peso en kg")
    dimensiones = models.CharField(max_length=100, blank=True, null=True, help_text="Largo x Ancho x Alto")
    color = models.CharField(max_length=50, blank=True, null=True)
    talla = models.CharField(max_length=50, blank=True, null=True)
    marca = models.CharField(max_length=100, blank=True, null=True)
    
    # Inventory settings
    stock_minimo = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_maximo = models.IntegerField(default=1000, validators=[MinValueValidator(0)])
    
    # Tracking settings
    requiere_numero_serie = models.BooleanField(default=False, help_text="Si requiere número de serie único")
    es_serializado = models.BooleanField(default=False, help_text="Si cada artículo tiene identificación única")
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.sku})"
    
    def cantidad_total(self):
        """Total quantity of articles across all warehouses"""
        return self.articulo_set.filter(estado='disponible').count() # type: ignore
    
    def cantidad_por_bodega(self):
        """Dictionary of quantities per warehouse"""
        from collections import defaultdict
        cantidades = defaultdict(int)
        for articulo in self.articulo_set.filter(estado='disponible'): # type: ignore
            cantidades[articulo.bodega.nombre] += 1
        return dict(cantidades)
    
    def esta_en_stock(self):
        """Check if product has available articles"""
        return self.articulo_set.filter(estado='disponible').exists() # type: ignore
    
    def necesita_restock(self):
        """Check if total stock is below minimum"""
        return self.cantidad_total() <= self.stock_minimo
    
    def bodegas_con_stock(self):
        """Return warehouses that have this product available"""
        return list(set(articulo.bodega for articulo in self.articulo_set.filter(estado='disponible'))) # type: ignore
    
    def cantidad_en_bodega(self, bodega):
        """Get quantity of this product in a specific warehouse"""
        return self.articulo_set.filter(bodega=bodega, estado='disponible').count() # type: ignore
    
    def articulos_por_estado(self):
        """Dictionary showing count of articles by state"""
        from collections import defaultdict
        estados = defaultdict(int)
        for articulo in self.articulo_set.all(): # type: ignore
            estados[articulo.get_estado_display()] += 1
        return dict(estados)


class Bodega(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bodegas_responsable')
    
    capacidad_maxima = models.IntegerField(blank=True, null=True, help_text="Capacidad máxima en unidades")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    



class ZonaBodega(models.Model):
    """Zones within a warehouse for better organization"""
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='zonas')
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20)
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['bodega', 'codigo']
        verbose_name_plural = "Zonas de Bodega"
    
    def __str__(self):
        return f"{self.bodega.nombre} - {self.nombre}"


class Articulo(models.Model):
    """Individual physical instance of a product"""
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
        ('dañado', 'Dañado'),
        ('en_transito', 'En Tránsito'),
        ('perdido', 'Perdido'),
        ('devuelto', 'Devuelto'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE)
    zona = models.ForeignKey(ZonaBodega, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Unique identifiers
    codigo_interno = models.CharField(max_length=100, unique=True, help_text="Código interno único del artículo")
    codigo_barras = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    lote = models.CharField(max_length=50, blank=True, null=True, help_text="Número de lote de fabricación")
    
    # Article-specific attributes (if different from product)
    precio_costo_real = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                          help_text="Precio real si difiere del producto")
    
    # Dates
    fecha_fabricacion = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    # Status
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    observaciones = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.codigo_interno:
            # Generate unique internal code if not provided
            self.codigo_interno = f"{self.producto.sku}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.producto.nombre} ({self.codigo_interno}) - {self.bodega.nombre}"
    
    def dias_en_inventario(self):
        """Days since article entered inventory"""
        from django.utils import timezone
        return (timezone.now().date() - self.fecha_entrada.date()).days
    
    
    class Meta:
        verbose_name_plural = "Artículos"


class MovimientoArticulo(models.Model):
    """Track movements of individual articles"""
    TIPOS_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('transferencia', 'Transferencia'),
        ('cambio_estado', 'Cambio de Estado'),
        ('ajuste_ubicacion', 'Ajuste de Ubicación'),
        ('devolucion', 'Devolución'),
    ]
    
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=25, choices=TIPOS_MOVIMIENTO)
    
    # Location changes
    bodega_origen = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='movimientos_articulos_salida')
    bodega_destino = models.ForeignKey(Bodega, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='movimientos_articulos_entrada')
    
    # State changes
    estado_anterior = models.CharField(max_length=20, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=20, blank=True, null=True)
    
    # Reference data
    numero_documento = models.CharField(max_length=100, blank=True, null=True)
    motivo = models.TextField(help_text="Razón del movimiento")
    
    # Tracking
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.tipo_movimiento} - {self.articulo.codigo_interno}"
    
    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = "Movimientos de Artículos"


class Pedido(models.Model):
    """Modelo para manejar pedidos de productos"""
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('preparando', 'Preparando'),
        ('listo', 'Listo para Envío'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
        ('devuelto', 'Devuelto'),
    ]
    
    TIPOS_PEDIDO = [
        ('venta', 'Venta'),
        ('transferencia', 'Transferencia'),
        ('interno', 'Uso Interno'),
        ('devolucion', 'Devolución'),
    ]
    
    # Identificación
    numero_pedido = models.CharField(max_length=50, unique=True, help_text="Número único del pedido")
    tipo_pedido = models.CharField(max_length=15, choices=TIPOS_PEDIDO, default='venta')
    estado = models.CharField(max_length=15, choices=ESTADOS_PEDIDO, default='pendiente')
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_requerida = models.DateTimeField(help_text="Fecha cuando se necesita el pedido")
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Referencias
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pedidos_creados')
    usuario_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_asignados')
    
    # Información del cliente/destino
    cliente_nombre = models.CharField(max_length=200, blank=True, null=True)
    cliente_email = models.EmailField(blank=True, null=True)
    cliente_telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion_entrega = models.TextField(blank=True, null=True)
    
    # Notas y observaciones
    notas = models.TextField(blank=True, null=True)
    observaciones_internas = models.TextField(blank=True, null=True)
    
    # Totales (se calculan automáticamente)
    total_articulos = models.PositiveIntegerField(default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    def save(self, *args, **kwargs):
        # Generar número de pedido si no existe
        if not self.numero_pedido:
            import uuid
            self.numero_pedido = f"PED-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Calcula y actualiza los totales del pedido"""
        detalles = self.detalles.all()
        self.total_articulos = sum(detalle.cantidad for detalle in detalles)
        self.valor_total = sum(detalle.subtotal() for detalle in detalles)
        self.save(update_fields=['total_articulos', 'valor_total'])
    
    def puede_ser_procesado(self):
        """Verifica si el pedido puede ser procesado (hay stock suficiente)"""
        for detalle in self.detalles.all():
            if not detalle.verificar_disponibilidad():
                return False
        return True
    
    def obtener_ubicaciones_productos(self):
        """Retorna productos, cantidades y ubicaciones en bodega para este pedido"""
        ubicaciones = []
        for detalle in self.detalles.select_related('producto'):
            # Buscar artículos disponibles del producto
            articulos_disponibles = Articulo.objects.filter(
                producto=detalle.producto,
                estado='disponible'
            ).select_related('bodega', 'zona')
            
            cantidad_requerida = detalle.cantidad
            cantidad_encontrada = 0
            ubicaciones_producto = []
            
            # Agrupar por bodega
            bodegas_disponibles = {}
            for articulo in articulos_disponibles:
                bodega_key = articulo.bodega.nombre
                if bodega_key not in bodegas_disponibles:
                    bodegas_disponibles[bodega_key] = {
                        'bodega': articulo.bodega,
                        'articulos': [],
                        'cantidad': 0
                    }
                bodegas_disponibles[bodega_key]['articulos'].append(articulo)
                bodegas_disponibles[bodega_key]['cantidad'] += 1
            
            # Seleccionar artículos hasta cumplir la cantidad requerida
            for bodega_info in bodegas_disponibles.values():
                if cantidad_encontrada >= cantidad_requerida:
                    break
                
                cantidad_en_esta_bodega = min(
                    bodega_info['cantidad'],
                    cantidad_requerida - cantidad_encontrada
                )
                
                if cantidad_en_esta_bodega > 0:
                    ubicaciones_producto.append({
                        'bodega': bodega_info['bodega'].nombre,
                        'bodega_id': bodega_info['bodega'].id,
                        'codigo_bodega': bodega_info['bodega'].codigo,
                        'cantidad_disponible': cantidad_en_esta_bodega,
                        'articulos': bodega_info['articulos'][:cantidad_en_esta_bodega]
                    })
                    cantidad_encontrada += cantidad_en_esta_bodega
            
            ubicaciones.append({
                'producto_id': detalle.producto.id,
                'producto_nombre': detalle.producto.nombre,
                'producto_sku': detalle.producto.sku,
                'cantidad_pedida': detalle.cantidad,
                'cantidad_disponible': cantidad_encontrada,
                'cantidad_faltante': max(0, detalle.cantidad - cantidad_encontrada),
                'precio_unitario': detalle.precio_unitario,
                'subtotal': detalle.subtotal(),
                'ubicaciones': ubicaciones_producto,
                'completamente_disponible': cantidad_encontrada >= detalle.cantidad
            })
        
        return ubicaciones
    
    def __str__(self):
        return f"{self.numero_pedido} - {self.cliente_nombre or 'Sin cliente'}"
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name_plural = "Pedidos"


class DetallePedido(models.Model):
    """Detalle de productos en un pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Información adicional
    notas = models.TextField(blank=True, null=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    def subtotal(self):
        """Calcula el subtotal para este detalle"""
        return self.cantidad * self.precio_unitario
    
    def verificar_disponibilidad(self):
        """Verifica si hay suficiente stock disponible del producto"""
        cantidad_disponible = Articulo.objects.filter(
            producto=self.producto,
            estado='disponible'
        ).count()
        return cantidad_disponible >= self.cantidad
    
    def save(self, *args, **kwargs):
        # Si no se especifica precio, usar el precio de venta del producto
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio_venta
        super().save(*args, **kwargs)
        
        # Recalcular totales del pedido
        self.pedido.calcular_totales()
    
    def delete(self, *args, **kwargs):
        pedido = self.pedido
        result = super().delete(*args, **kwargs)
        # Recalcular totales después de eliminar
        pedido.calcular_totales()
        return result
    
    def __str__(self):
        return f"{self.pedido.numero_pedido} - {self.producto.nombre} x{self.cantidad}"
    
    class Meta:
        unique_together = ['pedido', 'producto']  # Un producto por pedido
        verbose_name_plural = "Detalles de Pedidos"





