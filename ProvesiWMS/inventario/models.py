from decimal import Decimal
from django.db import models, transaction
from django.db.models import F

# =========================
# MODELOS DE INVENTARIO
# =========================

class Bodega(models.Model):
    """
    Representa una bodega física donde se almacenan productos.
    """
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
    
    def obtener_capacidad_total(self):
        """Obtiene la capacidad total de todas las ubicaciones en la bodega"""
        from django.db.models import Sum
        result = UbicacionBodega.objects.filter(bodega=self).aggregate(
            total=Sum('capacidad_total')
        )['total']
        return result or 0

class UbicacionBodega(models.Model):
    """
    Ubicación específica dentro de una bodega (pasillo, estante, nivel).
    """
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE)
    pasillo = models.CharField(max_length=50)
    estante = models.CharField(max_length=50)
    nivel = models.CharField(max_length=50)
    capacidad_total = models.IntegerField()
    capacidad_disponible = models.IntegerField()

    def __str__(self):
        return f"{self.bodega.nombre} - Pasillo {self.pasillo}, Estante {self.estante}, Nivel {self.nivel}"
    
    def esta_llena(self):
        """Verifica si la ubicación está al máximo de capacidad"""
        return self.capacidad_disponible == 0
    
    def ocupar_espacio(self, cantidad=1):
        """
        Ocupa espacio en la ubicación de forma thread-safe y atómica.
        
        Estrategia:
        1. Usa select_for_update() para bloquear la fila durante la transacción
        2. Usa F() expression para actualización atómica a nivel de base de datos
        3. Maneja el caso donde capacidad_disponible < cantidad sin condiciones de carrera
        
        Args:
            cantidad (int): Número de espacios a ocupar (default: 1)
            
        Returns:
            bool: True si se ocupó el espacio exitosamente, False si no hay capacidad
        """
        with transaction.atomic():
            # Bloquea la fila para esta transacción, bloqueando a otros threads
            # En PostgreSQL/MySQL esto usa FOR UPDATE
            ubicacion = UbicacionBodega.objects.select_for_update().get(pk=self.pk)
            
            # Verifica capacidad ANTES de la actualización
            if ubicacion.capacidad_disponible < cantidad:
                return False
            
            # Actualización atómica usando F() expression
            # Esto se traduce a: UPDATE ... SET capacidad_disponible = capacidad_disponible - cantidad
            # La operación es atómica a nivel de base de datos
            UbicacionBodega.objects.filter(pk=self.pk).update(
                capacidad_disponible=F('capacidad_disponible') - cantidad
            )
            
            # Refresca el objeto actual para reflejar el cambio
            self.refresh_from_db()
            return True

class Producto(models.Model):
    """
    Información general de un producto.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    dimensiones = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    talla = models.CharField(max_length=50)
    marca = models.CharField(max_length=100)
    cantidad_stock = models.IntegerField()

    def __str__(self):
        return self.nombre
    
    def calcular_margen_ganancia(self):
        """Calcula el margen de ganancia del producto"""
        if self.precio_costo > 0:
            return ((self.precio_venta - self.precio_costo) / self.precio_costo) * 100
        return 0
    
    def hay_stock(self):
        """Verifica si hay stock disponible"""
        return self.cantidad_stock > 0
    
    def reducir_stock(self, cantidad):
        """Reduce el stock del producto"""
        if cantidad <= self.cantidad_stock:
            self.cantidad_stock -= cantidad
            self.save()
            return True
        return False

class Articulo(models.Model):
    """
    Representa una unidad física de un producto, identificada por código de barras.
    """
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    codigo_barras = models.CharField(max_length=100, unique=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    fecha_salida = models.DateField(null=True, blank=True)
    ubicacion = models.ForeignKey('UbicacionBodega', on_delete=models.CASCADE)

    def __str__(self):
        return self.codigo_barras
    
    def marcar_salida(self):
        """Marca la fecha de salida del artículo"""
        from django.utils import timezone
        self.fecha_salida = timezone.now().date()
        self.save()

# =========================
# MODELOS DE USUARIOS Y CLIENTES
# =========================

class Cliente(models.Model):
    """
    Información de clientes.
    """
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Usuario(models.Model):
    """
    Usuarios del sistema (administradores, empleados, clientes).
    """
    ROLES_USUARIO = [
        ('admin', 'Administrador'),
        ('empleado', 'Empleado'),
        ('cliente', 'Cliente')
    ]
    nombre_usuario = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    rol = models.CharField(max_length=50, choices=ROLES_USUARIO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_usuario

# =========================
# MODELOS DE VENTAS Y PEDIDOS
# =========================

class Cotizacion(models.Model):
    """
    Cotización realizada a un cliente.
    """
    cliente = models.ForeignKey('Cliente', on_delete=models.DO_NOTHING)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    validez_hasta = models.DateTimeField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50)  # Ejemplo: 'pendiente'

    def __str__(self):
        return f"Cotización {self.id} - {self.cliente.nombre}" # type: ignore
    
    def esta_vigente(self):
        """Verifica si la cotización está vigente"""
        from django.utils import timezone
        return timezone.now() <= self.validez_hasta

class Pedido(models.Model):
    """
    Pedido realizado por un cliente, puede estar asociado a una cotización.
    """
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('preparando', 'Preparando'),
        ('listo', 'Listo para Envío'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
        ('devuelto', 'Devuelto'),
    ]
    cotizacion = models.ForeignKey('Cotizacion', on_delete=models.DO_NOTHING, null=True, blank=True)
    numero_pedido = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    cliente = models.ForeignKey('Cliente', on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.numero_pedido
    
    def calcular_total(self):
        """Calcula el total del pedido sumando todos los productos"""
        from django.db.models import Sum, F
        total = PedidoProducto.objects.filter(pedido=self).aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total']
        return total or Decimal('0.00')
    
    def puede_cancelar(self):
        """Verifica si el pedido puede ser cancelado"""
        return self.estado in ['pendiente', 'preparando']
    
    def marcar_completado(self):
        """Marca el pedido como completado"""
        from django.utils import timezone
        if self.estado != 'entregado':
            self.estado = 'entregado'
            self.fecha_completado = timezone.now()
            self.save()

class PedidoProducto(models.Model):
    """
    Relación intermedia entre Pedido y Producto, con cantidad y precio unitario.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='productos')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['pedido', 'producto']

    def subtotal(self):
        return self.cantidad * self.precio_unitario

class PedidoArticulo(models.Model):
    """
    Relación entre Pedido y Artículo (unidad física).
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    articulo = models.ForeignKey('Articulo', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['pedido', 'articulo']

# =========================
# MODELOS DE PROCESOS DE PEDIDO
# =========================

class DevolucionPedido(models.Model):
    """
    Registro de devoluciones de pedidos.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()
    estado = models.CharField(max_length=50)  # Ejemplo: 'pendiente', 'procesado'

class ReclamoPedido(models.Model):
    """
    Registro de reclamos asociados a un pedido.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    fecha_reclamo = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    estado = models.CharField(max_length=50)  # Ejemplo: 'abierto', 'cerrado'

class AlistamientoPedido(models.Model):
    """
    Proceso de alistamiento de un pedido por un empleado.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    empleado = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    fecha_alistamiento = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)  # Ejemplo: 'en progreso', 'completado'

class EmpaquePedido(models.Model):
    """
    Proceso de empaque de un pedido.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    empleado = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    fecha_empaque = models.DateTimeField(auto_now_add=True)
    tipo_empaque = models.CharField(max_length=100)  # Ejemplo: 'caja', 'sobre'
    estado = models.CharField(max_length=50)

class VerificacionPedido(models.Model):
    """
    Proceso de verificación de un pedido antes del envío.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    empleado = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    fecha_verificacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)  # Ejemplo: 'aprobado', 'rechazado'
    observaciones = models.TextField(null=True, blank=True)

class GuiaEnvioPedido(models.Model):
    """
    Información de la guía de envío asociada a un pedido.
    """
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE)
    numero_guia = models.CharField(max_length=100, unique=True)
    empresa_transporte = models.CharField(max_length=100)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50)  # Ejemplo: 'en tránsito', 'entregado'

class Factura(models.Model):
    """
    Factura generada para un pedido.
    """
    pedido = models.OneToOneField('Pedido', on_delete=models.DO_NOTHING)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuentos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    metodo_pago = models.CharField(max_length=50)
    
    def __str__(self):
        return f"Factura {self.id} - Pedido {self.pedido.numero_pedido}" # type: ignore
    
    def calcular_total_neto(self):
        """Calcula el total neto después de descuentos"""
        return self.total - self.descuentos


