from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    Bodega, UbicacionBodega, Producto, Articulo, Cliente, Usuario,
    Cotizacion, Pedido, PedidoProducto, PedidoArticulo, Factura
)

# =========================
# TESTS DE MODELOS
# =========================

class BodegaModelTest(TestCase):
    """
    Tests para el modelo Bodega y sus métodos.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.bodega = Bodega.objects.create(
            nombre="Bodega Central",
            ciudad="Bogotá",
            direccion="Calle 123 #45-67"
        )
    
    def test_str_method(self):
        """Test del método __str__ de Bodega."""
        self.assertEqual(str(self.bodega), "Bodega Central")
    
    def test_obtener_capacidad_total_sin_ubicaciones(self):
        """Test de capacidad total cuando no hay ubicaciones."""
        self.assertEqual(self.bodega.obtener_capacidad_total(), 0)
    
    def test_obtener_capacidad_total_con_ubicaciones(self):
        """Test de capacidad total con ubicaciones."""
        UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="A1",
            estante="E1",
            nivel="N1",
            capacidad_total=100,
            capacidad_disponible=80
        )
        UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="A2",
            estante="E2",
            nivel="N2",
            capacidad_total=150,
            capacidad_disponible=120
        )
        self.assertEqual(self.bodega.obtener_capacidad_total(), 250)


class UbicacionBodegaModelTest(TestCase):
    """
    Tests para el modelo UbicacionBodega y sus métodos.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.bodega = Bodega.objects.create(
            nombre="Bodega Test",
            ciudad="Test City",
            direccion="Test Address"
        )
        self.ubicacion = UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="A1",
            estante="E1",
            nivel="N1",
            capacidad_total=100,
            capacidad_disponible=50
        )
    
    def test_str_method(self):
        """Test del método __str__ de UbicacionBodega."""
        expected = "Bodega Test - Pasillo A1, Estante E1, Nivel N1"
        self.assertEqual(str(self.ubicacion), expected)
    
    def test_esta_llena_false(self):
        """Test cuando la ubicación no está llena."""
        self.assertFalse(self.ubicacion.esta_llena())
    
    def test_esta_llena_true(self):
        """Test cuando la ubicación está llena."""
        self.ubicacion.capacidad_disponible = 0
        self.ubicacion.save()
        self.assertTrue(self.ubicacion.esta_llena())
    
    def test_ocupar_espacio_exitoso(self):
        """Test de ocupar espacio exitosamente."""
        inicial = self.ubicacion.capacidad_disponible
        resultado = self.ubicacion.ocupar_espacio(20)
        self.assertTrue(resultado)
        self.ubicacion.refresh_from_db()
        self.assertEqual(self.ubicacion.capacidad_disponible, inicial - 20)
    
    def test_ocupar_espacio_insuficiente(self):
        """Test cuando no hay suficiente espacio."""
        resultado = self.ubicacion.ocupar_espacio(60)  # Más de lo disponible (50)
        self.assertFalse(resultado)


class ProductoModelTest(TestCase):
    """
    Tests para el modelo Producto y sus métodos.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            descripcion="Descripción del producto test",
            precio_costo=Decimal('100.00'),
            precio_venta=Decimal('150.00'),
            peso=Decimal('1.5'),
            dimensiones="10x20x30",
            color="Azul",
            talla="M",
            marca="TestMarca",
            cantidad_stock=25
        )
    
    def test_str_method(self):
        """Test del método __str__ de Producto."""
        self.assertEqual(str(self.producto), "Producto Test")
    
    def test_calcular_margen_ganancia(self):
        """Test del cálculo de margen de ganancia."""
        margen = self.producto.calcular_margen_ganancia()
        self.assertEqual(margen, 50.0)  # (150-100)/100 * 100 = 50%
    
    def test_calcular_margen_ganancia_costo_cero(self):
        """Test margen cuando el costo es cero."""
        self.producto.precio_costo = Decimal('0.00')
        self.producto.save()
        margen = self.producto.calcular_margen_ganancia()
        self.assertEqual(margen, 0)
    
    def test_hay_stock_true(self):
        """Test cuando hay stock disponible."""
        self.assertTrue(self.producto.hay_stock())
    
    def test_hay_stock_false(self):
        """Test cuando no hay stock disponible."""
        self.producto.cantidad_stock = 0
        self.producto.save()
        self.assertFalse(self.producto.hay_stock())
    
    def test_reducir_stock_exitoso(self):
        """Test de reducción de stock exitosa."""
        stock_inicial = self.producto.cantidad_stock
        resultado = self.producto.reducir_stock(10)
        self.assertTrue(resultado)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.cantidad_stock, stock_inicial - 10)
    
    def test_reducir_stock_insuficiente(self):
        """Test cuando el stock es insuficiente."""
        resultado = self.producto.reducir_stock(30)  # Más del stock disponible (25)
        self.assertFalse(resultado)


class ClienteModelTest(TestCase):
    """
    Tests para el modelo Cliente.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            email="cliente@test.com",
            telefono="123456789",
            direccion="Dirección Test",
            ciudad="Ciudad Test"
        )
    
    def test_str_method(self):
        """Test del método __str__ de Cliente."""
        self.assertEqual(str(self.cliente), "Cliente Test")


class PedidoModelTest(TestCase):
    """
    Tests para el modelo Pedido y sus métodos.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            email="cliente@test.com",
            telefono="123456789",
            direccion="Dirección Test",
            ciudad="Ciudad Test"
        )
        self.pedido = Pedido.objects.create(
            numero_pedido="PED-000001",
            cliente=self.cliente,
            estado='pendiente'
        )
        self.producto1 = Producto.objects.create(
            nombre="Producto 1",
            descripcion="Desc 1",
            precio_costo=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Rojo",
            talla="S",
            marca="Marca1",
            cantidad_stock=20
        )
        self.producto2 = Producto.objects.create(
            nombre="Producto 2",
            descripcion="Desc 2",
            precio_costo=Decimal('75.00'),
            precio_venta=Decimal('150.00'),
            peso=Decimal('2.0'),
            dimensiones="20x20x20",
            color="Verde",
            talla="M",
            marca="Marca2",
            cantidad_stock=15
        )
    
    def test_str_method(self):
        """Test del método __str__ de Pedido."""
        self.assertEqual(str(self.pedido), "PED-000001")
    
    def test_calcular_total_sin_productos(self):
        """Test del cálculo de total sin productos."""
        total = self.pedido.calcular_total()
        self.assertEqual(total, Decimal('0.00'))
    
    def test_calcular_total_con_productos(self):
        """Test del cálculo de total con productos."""
        PedidoProducto.objects.create(
            pedido=self.pedido,
            producto=self.producto1,
            cantidad=2,
            precio_unitario=Decimal('100.00')
        )
        PedidoProducto.objects.create(
            pedido=self.pedido,
            producto=self.producto2,
            cantidad=1,
            precio_unitario=Decimal('150.00')
        )
        
        total = self.pedido.calcular_total()
        self.assertEqual(total, Decimal('350.00'))  # (2*100) + (1*150) = 350
    
    def test_puede_cancelar_pendiente(self):
        """Test si puede cancelar cuando está pendiente."""
        self.assertTrue(self.pedido.puede_cancelar())
    
    def test_puede_cancelar_preparando(self):
        """Test si puede cancelar cuando está preparando."""
        self.pedido.estado = 'preparando'
        self.pedido.save()
        self.assertTrue(self.pedido.puede_cancelar())
    
    def test_no_puede_cancelar_entregado(self):
        """Test que no puede cancelar cuando está entregado."""
        self.pedido.estado = 'entregado'
        self.pedido.save()
        self.assertFalse(self.pedido.puede_cancelar())
    
    def test_marcar_completado(self):
        """Test de marcar pedido como completado."""
        self.assertIsNone(self.pedido.fecha_completado)
        self.pedido.marcar_completado()
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'entregado')
        self.assertIsNotNone(self.pedido.fecha_completado)


class PedidoProductoModelTest(TestCase):
    """
    Tests para el modelo PedidoProducto.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            email="cliente@test.com",
            telefono="123456789",
            direccion="Dirección Test",
            ciudad="Ciudad Test"
        )
        self.pedido = Pedido.objects.create(
            numero_pedido="PED-000001",
            cliente=self.cliente
        )
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            descripcion="Desc Test",
            precio_costo=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Azul",
            talla="M",
            marca="TestMarca",
            cantidad_stock=10
        )
        self.pedido_producto = PedidoProducto.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=3,
            precio_unitario=Decimal('100.00')
        )
    
    def test_subtotal(self):
        """Test del cálculo de subtotal."""
        subtotal = self.pedido_producto.subtotal()
        self.assertEqual(subtotal, Decimal('300.00'))  # 3 * 100 = 300


# =========================
# TESTS DE VISTAS
# =========================

class IndexViewTest(TestCase):
    """
    Tests para la vista principal (dashboard).
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        # Crear datos de prueba
        Bodega.objects.create(nombre="Bodega 1", ciudad="Ciudad 1", direccion="Dir 1")
        Bodega.objects.create(nombre="Bodega 2", ciudad="Ciudad 2", direccion="Dir 2")
        
        Cliente.objects.create(
            nombre="Cliente 1", 
            email="cliente1@test.com",
            telefono="123",
            direccion="Dir 1",
            ciudad="Ciudad 1"
        )
        
        Producto.objects.create(
            nombre="Producto 1",
            descripcion="Desc 1",
            precio_costo=Decimal('50'),
            precio_venta=Decimal('100'),
            peso=Decimal('1'),
            dimensiones="10x10x10",
            color="Rojo",
            talla="S",
            marca="Marca1",
            cantidad_stock=0  # Sin stock
        )
    
    def test_index_view_get(self):
        """Test de la vista principal con GET."""
        url = reverse('inventario:index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard de Inventario")
        self.assertEqual(response.context['total_bodegas'], 2)
        self.assertEqual(response.context['total_clientes'], 1)
        self.assertEqual(response.context['productos_sin_stock'], 1)


class ProductoViewsTest(TestCase):
    """
    Tests para las vistas de productos.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.producto1 = Producto.objects.create(
            nombre="Producto Test 1",
            descripcion="Descripción 1",
            precio_costo=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Azul",
            talla="M",
            marca="TestMarca",
            cantidad_stock=10
        )
        self.producto2 = Producto.objects.create(
            nombre="Producto Test 2",
            descripcion="Descripción 2",
            precio_costo=Decimal('75.00'),
            precio_venta=Decimal('150.00'),
            peso=Decimal('2.0'),
            dimensiones="20x20x20",
            color="Rojo",
            talla="L",
            marca="OtraMarca",
            cantidad_stock=0  # Sin stock
        )
    
    def test_producto_list_view(self):
        """Test de la vista lista de productos."""
        url = reverse('inventario:productos_lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Producto Test 1")
        self.assertContains(response, "Producto Test 2")
    
    def test_producto_list_view_with_search(self):
        """Test de búsqueda en la lista de productos."""
        url = reverse('inventario:productos_lista')
        response = self.client.get(url, {'search': 'TestMarca'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Producto Test 1")
        self.assertNotContains(response, "Producto Test 2")
    
    def test_producto_detail_view(self):
        """Test de la vista detalle de producto."""
        url = reverse('inventario:producto_detalle', kwargs={'pk': self.producto1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['producto'], self.producto1)
    
    def test_productos_sin_stock_view(self):
        """Test de la vista de productos sin stock."""
        url = reverse('inventario:productos_sin_stock')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Producto Test 2")
        self.assertNotContains(response, "Producto Test 1")


class BodegaViewsTest(TestCase):
    """
    Tests para las vistas de bodegas.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.bodega = Bodega.objects.create(
            nombre="Bodega Test",
            ciudad="Ciudad Test",
            direccion="Dirección Test"
        )
    
    def test_bodega_list_view(self):
        """Test de la vista lista de bodegas."""
        url = reverse('inventario:bodegas_lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bodega Test")
    
    def test_bodega_detail_view(self):
        """Test de la vista detalle de bodega."""
        url = reverse('inventario:bodega_detalle', kwargs={'pk': self.bodega.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['bodega'], self.bodega)


# =========================
# TESTS DE API
# =========================

class APIViewsTest(TestCase):
    """
    Tests para las vistas de API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.producto = Producto.objects.create(
            nombre="Producto API Test",
            descripcion="Desc API",
            precio_costo=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Verde",
            talla="M",
            marca="APIMarca",
            cantidad_stock=15
        )
        
        self.cliente = Cliente.objects.create(
            nombre="Cliente API",
            email="api@test.com",
            telefono="123456789",
            direccion="Dir API",
            ciudad="Ciudad API"
        )
        
        self.pedido = Pedido.objects.create(
            numero_pedido="PED-API-001",
            cliente=self.cliente
        )
        
        PedidoProducto.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal('100.00')
        )
    
    def test_api_productos_stock(self):
        """Test del endpoint API de stock de productos."""
        url = reverse('inventario:api_productos_stock')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nombre'], 'Producto API Test')
        self.assertEqual(data[0]['cantidad_stock'], 15)
    
    def test_api_buscar_productos(self):
        """Test del endpoint API de búsqueda de productos."""
        url = reverse('inventario:api_buscar_productos')
        response = self.client.get(url, {'q': 'API'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nombre'], 'Producto API Test')
    
    def test_api_buscar_productos_query_corto(self):
        """Test de búsqueda con query muy corto."""
        url = reverse('inventario:api_buscar_productos')
        response = self.client.get(url, {'q': 'A'})  # Menos de 2 caracteres
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])
    
    def test_api_pedido_total(self):
        """Test del endpoint API de total de pedido."""
        url = reverse('inventario:api_pedido_total', kwargs={'pedido_id': self.pedido.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['pedido_id'], self.pedido.pk)
        self.assertEqual(data['total'], 200.0)  # 2 * 100 = 200
        self.assertEqual(data['estado'], 'pendiente')
    
    def test_api_pedido_total_not_found(self):
        """Test del endpoint con pedido inexistente."""
        url = reverse('inventario:api_pedido_total', kwargs={'pedido_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 400)


# =========================
# TESTS DE INTEGRACIÓN
# =========================

class IntegrationTest(TestCase):
    """
    Tests de integración que prueban flujos completos.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        
        # Crear datos base
        self.bodega = Bodega.objects.create(
            nombre="Bodega Principal",
            ciudad="Bogotá",
            direccion="Calle Principal 123"
        )
        
        self.ubicacion = UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="A1",
            estante="E1",
            nivel="N1",
            capacidad_total=1000,
            capacidad_disponible=800
        )
        
        self.cliente = Cliente.objects.create(
            nombre="Cliente Principal",
            email="principal@test.com",
            telefono="123456789",
            direccion="Dirección Principal",
            ciudad="Bogotá"
        )
        
        self.producto = Producto.objects.create(
            nombre="Producto Principal",
            descripcion="Producto para integración",
            precio_costo=Decimal('100.00'),
            precio_venta=Decimal('200.00'),
            peso=Decimal('2.5'),
            dimensiones="30x40x50",
            color="Azul",
            talla="L",
            marca="MarcaPrincipal",
            cantidad_stock=50
        )
    
    def test_flujo_completo_pedido(self):
        """Test del flujo completo de creación de pedido."""
        # 1. Verificar stock inicial
        stock_inicial = self.producto.cantidad_stock
        self.assertEqual(stock_inicial, 50)
        
        # 2. Crear pedido
        pedido = Pedido.objects.create(
            numero_pedido="PED-INTEGRATION-001",
            cliente=self.cliente,
            estado='pendiente'
        )
        
        # 3. Agregar producto al pedido
        pedido_producto = PedidoProducto.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=5,
            precio_unitario=self.producto.precio_venta
        )
        
        # 4. Reducir stock
        resultado = self.producto.reducir_stock(5)
        self.assertTrue(resultado)
        
        # 5. Verificar stock actualizado
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.cantidad_stock, 45)
        
        # 6. Verificar total del pedido
        total = pedido.calcular_total()
        self.assertEqual(total, Decimal('1000.00'))  # 5 * 200 = 1000
        
        # 7. Completar pedido
        pedido.marcar_completado()
        self.assertEqual(pedido.estado, 'entregado')
        self.assertIsNotNone(pedido.fecha_completado)
    
    def test_flujo_ubicacion_bodega(self):
        """Test del flujo de gestión de ubicaciones en bodega."""
        # 1. Verificar capacidad inicial
        capacidad_inicial = self.ubicacion.capacidad_disponible
        self.assertEqual(capacidad_inicial, 800)
        
        # 2. Ocupar espacio
        resultado = self.ubicacion.ocupar_espacio(100)
        self.assertTrue(resultado)
        
        # 3. Verificar capacidad actualizada
        self.ubicacion.refresh_from_db()
        self.assertEqual(self.ubicacion.capacidad_disponible, 700)
        
        # 4. Intentar ocupar más espacio del disponible
        resultado = self.ubicacion.ocupar_espacio(800)  # Más del disponible
        self.assertFalse(resultado)
        
        # 5. Verificar que la capacidad no cambió
        self.ubicacion.refresh_from_db()
        self.assertEqual(self.ubicacion.capacidad_disponible, 700)
        
        # 6. Verificar capacidad total de la bodega
        capacidad_total = self.bodega.obtener_capacidad_total()
        self.assertEqual(capacidad_total, 1000)


# =========================
# TESTS CRUD COMPLETOS
# =========================

class ProductoCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de productos via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
    
    def test_crear_producto_api(self):
        """Test de crear producto via API."""
        url = reverse('inventario:crear_producto')
        producto_data = {
            "nombre": "Laptop Test CRUD",
            "descripcion": "Laptop para pruebas de CRUD",
            "marca": "TestBrand",
            "precio_costo": 800.00,
            "precio_venta": 1200.00,
            "cantidad_stock": 10,
            "peso": 2.5,
            "dimensiones": "35x25x2 cm",
            "color": "Negro",
            "talla": "15 pulgadas"
        }
        
        response = self.client.post(url, 
                                  data=json.dumps(producto_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('producto', data)
        self.assertEqual(data['producto']['nombre'], 'Laptop Test CRUD')
        
        # Verificar que el producto se creó en la base de datos
        producto = Producto.objects.get(nombre='Laptop Test CRUD')
        self.assertEqual(producto.marca, 'TestBrand')
        self.assertEqual(producto.precio_costo, Decimal('800.00'))
        self.assertEqual(producto.cantidad_stock, 10)
    
    def test_actualizar_producto_api(self):
        """Test de actualizar producto via API."""
        # Crear producto inicial
        producto = Producto.objects.create(
            nombre="Producto Original",
            descripcion="Descripción original",
            precio_costo=Decimal('100.00'),
            precio_venta=Decimal('200.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Azul",
            talla="M",
            marca="MarcaOriginal",
            cantidad_stock=5
        )
        
        url = reverse('inventario:actualizar_producto', kwargs={'producto_id': producto.pk})
        update_data = {
            "nombre": "Producto Actualizado",
            "precio_venta": 250.00,
            "cantidad_stock": 15,
            "color": "Rojo"
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Producto Actualizado')
        self.assertEqual(producto.precio_venta, Decimal('250.00'))
        self.assertEqual(producto.cantidad_stock, 15)
        self.assertEqual(producto.color, 'Rojo')
    
    def test_eliminar_producto_api(self):
        """Test de eliminar producto via API."""
        # Crear producto para eliminar
        producto = Producto.objects.create(
            nombre="Producto a Eliminar",
            descripcion="Para eliminar",
            precio_costo=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Verde",
            talla="S",
            marca="MarcaEliminar",
            cantidad_stock=3
        )
        producto_id = producto.pk
        
        url = reverse('inventario:eliminar_producto', kwargs={'producto_id': producto.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar que el producto fue eliminado
        with self.assertRaises(Producto.DoesNotExist):
            Producto.objects.get(pk=producto_id)


class BodegaCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de bodegas via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
    
    def test_crear_bodega_api(self):
        """Test de crear bodega via API."""
        url = reverse('inventario:crear_bodega')
        bodega_data = {
            "nombre": "Bodega Test CRUD",
            "ciudad": "Bogotá",
            "direccion": "Calle 123 #45-67"
        }
        
        response = self.client.post(url,
                                  data=json.dumps(bodega_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('bodega', data)
        self.assertEqual(data['bodega']['nombre'], 'Bodega Test CRUD')
        
        # Verificar que la bodega se creó en la base de datos
        bodega = Bodega.objects.get(nombre='Bodega Test CRUD')
        self.assertEqual(bodega.ciudad, 'Bogotá')
        self.assertEqual(bodega.direccion, 'Calle 123 #45-67')
    
    def test_actualizar_bodega_api(self):
        """Test de actualizar bodega via API."""
        # Crear bodega inicial
        bodega = Bodega.objects.create(
            nombre="Bodega Original",
            ciudad="Ciudad Original",
            direccion="Dirección Original"
        )
        
        url = reverse('inventario:actualizar_bodega', kwargs={'bodega_id': bodega.pk})
        update_data = {
            "nombre": "Bodega Actualizada",
            "ciudad": "Medellín",
            "direccion": "Carrera 50 #30-20"
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        bodega.refresh_from_db()
        self.assertEqual(bodega.nombre, 'Bodega Actualizada')
        self.assertEqual(bodega.ciudad, 'Medellín')
        self.assertEqual(bodega.direccion, 'Carrera 50 #30-20')
    
    def test_eliminar_bodega_api(self):
        """Test de eliminar bodega via API."""
        # Crear bodega para eliminar
        bodega = Bodega.objects.create(
            nombre="Bodega a Eliminar",
            ciudad="Ciudad Temporal",
            direccion="Dirección Temporal"
        )
        bodega_id = bodega.pk
        
        url = reverse('inventario:eliminar_bodega', kwargs={'bodega_id': bodega.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar que la bodega fue eliminada
        with self.assertRaises(Bodega.DoesNotExist):
            Bodega.objects.get(pk=bodega_id)


class UbicacionBodegaCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de ubicaciones de bodega via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.bodega = Bodega.objects.create(
            nombre="Bodega para Ubicaciones",
            ciudad="Test City",
            direccion="Test Address"
        )
    
    def test_crear_ubicacion_api(self):
        """Test de crear ubicación via API."""
        url = reverse('inventario:crear_ubicacion_bodega')
        ubicacion_data = {
            "bodega_id": self.bodega.pk,
            "pasillo": "A",
            "estante": "1",
            "nivel": "2",
            "capacidad_total": 100
        }
        
        response = self.client.post(url,
                                  data=json.dumps(ubicacion_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('ubicacion', data)
        
        # Verificar que la ubicación se creó en la base de datos
        ubicacion = UbicacionBodega.objects.get(bodega=self.bodega, pasillo="A")
        self.assertEqual(ubicacion.estante, "1")
        self.assertEqual(ubicacion.nivel, "2")
        self.assertEqual(ubicacion.capacidad_total, 100)
    
    def test_actualizar_ubicacion_api(self):
        """Test de actualizar ubicación via API."""
        # Crear ubicación inicial
        ubicacion = UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="B",
            estante="2",
            nivel="1",
            capacidad_total=50,
            capacidad_disponible=50
        )
        
        url = reverse('inventario:actualizar_ubicacion_bodega', kwargs={'ubicacion_id': ubicacion.pk})
        update_data = {
            "pasillo": "C",
            "estante": "3",
            "nivel": "3",
            "capacidad_total": 150
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        ubicacion.refresh_from_db()
        self.assertEqual(ubicacion.pasillo, 'C')
        self.assertEqual(ubicacion.estante, '3')
        self.assertEqual(ubicacion.nivel, '3')
        self.assertEqual(ubicacion.capacidad_total, 150)
    
    def test_eliminar_ubicacion_api(self):
        """Test de eliminar ubicación via API."""
        # Crear ubicación para eliminar
        ubicacion = UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="D",
            estante="1",
            nivel="1",
            capacidad_total=75,
            capacidad_disponible=75
        )
        ubicacion_id = ubicacion.pk
        
        url = reverse('inventario:eliminar_ubicacion_bodega', kwargs={'ubicacion_id': ubicacion.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar que la ubicación fue eliminada
        with self.assertRaises(UbicacionBodega.DoesNotExist):
            UbicacionBodega.objects.get(pk=ubicacion_id)


class ClienteCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de clientes via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
    
    def test_crear_cliente_api(self):
        """Test de crear cliente via API."""
        url = reverse('inventario:crear_cliente')
        cliente_data = {
            "nombre": "Cliente Test CRUD",
            "email": "cliente.test@example.com",
            "telefono": "300-123-4567",
            "direccion": "Av. Siempre Viva 742",
            "ciudad": "Springfield"
        }
        
        response = self.client.post(url,
                                  data=json.dumps(cliente_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('cliente', data)
        self.assertEqual(data['cliente']['nombre'], 'Cliente Test CRUD')
        
        # Verificar que el cliente se creó en la base de datos
        cliente = Cliente.objects.get(nombre='Cliente Test CRUD')
        self.assertEqual(cliente.email, 'cliente.test@example.com')
        self.assertEqual(cliente.telefono, '300-123-4567')
    
    def test_actualizar_cliente_api(self):
        """Test de actualizar cliente via API."""
        # Crear cliente inicial
        cliente = Cliente.objects.create(
            nombre="Cliente Original",
            email="original@test.com",
            telefono="111-111-1111",
            direccion="Dirección Original",
            ciudad="Ciudad Original"
        )
        
        url = reverse('inventario:actualizar_cliente', kwargs={'cliente_id': cliente.pk})
        update_data = {
            "nombre": "Cliente Actualizado",
            "telefono": "300-987-6543",
            "ciudad": "Shelbyville"
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        cliente.refresh_from_db()
        self.assertEqual(cliente.nombre, 'Cliente Actualizado')
        self.assertEqual(cliente.telefono, '300-987-6543')
        self.assertEqual(cliente.ciudad, 'Shelbyville')
    
    def test_eliminar_cliente_api(self):
        """Test de eliminar cliente via API."""
        # Crear cliente para eliminar
        cliente = Cliente.objects.create(
            nombre="Cliente a Eliminar",
            email="eliminar@test.com",
            telefono="999-999-9999",
            direccion="Dirección Temporal",
            ciudad="Ciudad Temporal"
        )
        cliente_id = cliente.pk
        
        url = reverse('inventario:eliminar_cliente', kwargs={'cliente_id': cliente.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar que el cliente fue eliminado
        with self.assertRaises(Cliente.DoesNotExist):
            Cliente.objects.get(pk=cliente_id)


class UsuarioCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de usuarios via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
    
    def test_crear_usuario_api(self):
        """Test de crear usuario via API."""
        url = reverse('inventario:crear_usuario')
        usuario_data = {
            "nombre_usuario": "usuario_test_crud",
            "email": "usuario.test@example.com",
            "telefono": "300-555-0123",
            "rol": "empleado"
        }
        
        response = self.client.post(url,
                                  data=json.dumps(usuario_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('usuario', data)
        self.assertEqual(data['usuario']['nombre_usuario'], 'usuario_test_crud')
        
        # Verificar que el usuario se creó en la base de datos
        usuario = Usuario.objects.get(nombre_usuario='usuario_test_crud')
        self.assertEqual(usuario.email, 'usuario.test@example.com')
        self.assertEqual(usuario.rol, 'empleado')
    
    def test_actualizar_usuario_api(self):
        """Test de actualizar usuario via API."""
        # Crear usuario inicial
        usuario = Usuario.objects.create(
            nombre_usuario="usuario_original",
            email="original@test.com",
            telefono="111-111-1111",
            rol="empleado"
        )
        
        url = reverse('inventario:actualizar_usuario', kwargs={'usuario_id': usuario.pk})
        update_data = {
            "telefono": "300-555-9999",
            "rol": "admin"
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        usuario.refresh_from_db()
        self.assertEqual(usuario.telefono, '300-555-9999')
        self.assertEqual(usuario.rol, 'admin')
    
    def test_eliminar_usuario_api(self):
        """Test de eliminar usuario via API."""
        # Crear usuario para eliminar
        usuario = Usuario.objects.create(
            nombre_usuario="usuario_eliminar",
            email="eliminar@test.com",
            telefono="999-999-9999",
            rol="empleado"
        )
        usuario_id = usuario.pk
        
        url = reverse('inventario:eliminar_usuario', kwargs={'usuario_id': usuario.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar que el usuario fue eliminado
        with self.assertRaises(Usuario.DoesNotExist):
            Usuario.objects.get(pk=usuario_id)


class PedidoCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de pedidos via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.cliente_test = Cliente.objects.create(
            nombre="Cliente para Pedidos",
            email="pedidos@test.com",
            telefono="123-456-7890",
            direccion="Dir Test",
            ciudad="Ciudad Test"
        )
        self.producto_test = Producto.objects.create(
            nombre="Producto para Pedidos",
            descripcion="Desc Test",
            precio_costo=Decimal('50.00'),
            precio_venta=Decimal('100.00'),
            peso=Decimal('1.0'),
            dimensiones="10x10x10",
            color="Azul",
            talla="M",
            marca="MarcaTest",
            cantidad_stock=20
        )
    
    def test_crear_pedido_api(self):
        """Test de crear pedido via API."""
        url = reverse('inventario:crear_pedido')
        pedido_data = {
            "cliente_id": self.cliente_test.pk,
            "productos": [
                {
                    "producto_id": self.producto_test.pk,
                    "cantidad": 2,
                    "precio_unitario": 100.00
                }
            ]
        }
        
        response = self.client.post(url,
                                  data=json.dumps(pedido_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('pedido_id', data)
        
        # Verificar que el pedido se creó en la base de datos
        pedido = Pedido.objects.get(cliente=self.cliente_test)
        self.assertEqual(pedido.estado, 'pendiente')
        
        # Verificar que se creó el detalle del pedido
        detalle = PedidoProducto.objects.get(pedido=pedido)
        self.assertEqual(detalle.producto, self.producto_test)
        self.assertEqual(detalle.cantidad, 2)
    
    def test_actualizar_estado_pedido_api(self):
        """Test de actualizar estado de pedido via API."""
        # Crear pedido inicial
        pedido = Pedido.objects.create(
            numero_pedido="PED-TEST-001",
            cliente=self.cliente_test,
            estado='pendiente'
        )
        
        url = reverse('inventario:actualizar_estado_pedido', kwargs={'pedido_id': pedido.pk})
        update_data = {
            "estado": "preparando"
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'preparando')


class ArticuloCRUDViewsTest(TestCase):
    """
    Tests para operaciones CRUD completas de artículos via API.
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.client = Client()
        self.producto_test = Producto.objects.create(
            nombre="Producto para Artículos",
            descripcion="Desc Test",
            precio_costo=Decimal('30.00'),
            precio_venta=Decimal('60.00'),
            peso=Decimal('0.5'),
            dimensiones="5x5x5",
            color="Verde",
            talla="XS",
            marca="MarcaArticulo",
            cantidad_stock=50
        )
        
        self.bodega_test = Bodega.objects.create(
            nombre="Bodega para Artículos",
            ciudad="Test City",
            direccion="Test Address"
        )
        
        self.ubicacion_test = UbicacionBodega.objects.create(
            bodega=self.bodega_test,
            pasillo="A1",
            estante="E1",
            nivel="N1",
            capacidad_total=100,
            capacidad_disponible=80
        )
    
    def test_crear_articulo_api(self):
        """Test de crear artículo via API."""
        url = reverse('inventario:crear_articulo')
        articulo_data = {
            "codigo_barras": "ART-TEST-001",
            "producto_id": self.producto_test.pk,
            "ubicacion_id": self.ubicacion_test.pk
        }
        
        response = self.client.post(url,
                                  data=json.dumps(articulo_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        self.assertIn('articulo', data)
        self.assertEqual(data['articulo']['codigo_barras'], 'ART-TEST-001')
        
        # Verificar que el artículo se creó en la base de datos
        articulo = Articulo.objects.get(codigo_barras='ART-TEST-001')
        self.assertEqual(articulo.producto, self.producto_test)
        self.assertEqual(articulo.ubicacion, self.ubicacion_test)
    
    def test_actualizar_articulo_api(self):
        """Test de actualizar artículo via API."""
        # Crear artículo inicial
        articulo = Articulo.objects.create(
            codigo_barras="ART-ORIGINAL",
            producto=self.producto_test,
            ubicacion=self.ubicacion_test
        )
        
        url = reverse('inventario:actualizar_articulo', kwargs={'articulo_id': articulo.pk})
        update_data = {
            "codigo_barras": "ART-ACTUALIZADO"
        }
        
        response = self.client.put(url,
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar cambios en la base de datos
        articulo.refresh_from_db()
        self.assertEqual(articulo.codigo_barras, 'ART-ACTUALIZADO')
    
    def test_eliminar_articulo_api(self):
        """Test de eliminar artículo via API."""
        # Crear artículo para eliminar
        articulo = Articulo.objects.create(
            codigo_barras="ART-ELIMINAR",
            producto=self.producto_test,
            ubicacion=self.ubicacion_test
        )
        articulo_id = articulo.pk
        
        url = reverse('inventario:eliminar_articulo', kwargs={'articulo_id': articulo.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['success'], True)
        
        # Verificar que el artículo fue eliminado
        with self.assertRaises(Articulo.DoesNotExist):
            Articulo.objects.get(pk=articulo_id)
