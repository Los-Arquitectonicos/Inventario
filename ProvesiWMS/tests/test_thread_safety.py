"""
Test de thread-safety para el método ocupar_espacio()
"""
import threading
from django.test import TestCase
from inventario.models import Bodega, UbicacionBodega, Producto, Articulo


class ThreadSafetyTestCase(TestCase):
    """
    Tests para verificar que ocupar_espacio() es thread-safe
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.bodega = Bodega.objects.create(
            nombre="Bodega Test",
            ciudad="Ciudad Test",
            direccion="Dirección Test"
        )
        
        self.ubicacion = UbicacionBodega.objects.create(
            bodega=self.bodega,
            pasillo="A",
            estante="1",
            nivel="1",
            capacidad_total=1000,
            capacidad_disponible=1000
        )
        
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            descripcion="Descripción test",
            precio_costo=10.00,
            precio_venta=15.00,
            peso=1.0,
            dimensiones="10x10x10",
            color="Rojo",
            talla="M",
            marca="TestMarca",
            cantidad_stock=1000
        )
    
    def test_ocupar_espacio_thread_safe(self):
        """
        Test que verifica que múltiples threads pueden ocupar espacio
        concurrentemente sin crear inconsistencias.
        """
        num_threads = 50
        articulos_por_thread = 20
        total_esperado = num_threads * articulos_por_thread
        
        # Asegurar que hay capacidad suficiente
        self.assertEqual(self.ubicacion.capacidad_disponible, 1000)
        self.assertGreaterEqual(self.ubicacion.capacidad_disponible, total_esperado)
        
        errores = []
        articulos_creados = []
        lock = threading.Lock()
        
        def crear_articulos(thread_id):
            """Función que ejecuta cada thread"""
            for i in range(articulos_por_thread):
                try:
                    codigo_barras = f"TEST{thread_id:03d}{i:03d}"
                    
                    # Intentar ocupar espacio
                    if self.ubicacion.ocupar_espacio(cantidad=1):
                        # Crear artículo
                        articulo = Articulo.objects.create(
                            producto=self.producto,
                            codigo_barras=codigo_barras,
                            ubicacion=self.ubicacion
                        )
                        with lock:
                            articulos_creados.append(articulo)
                    else:
                        with lock:
                            errores.append(f"Thread {thread_id}: No pudo ocupar espacio para {codigo_barras}")
                
                except Exception as e:
                    with lock:
                        errores.append(f"Thread {thread_id}: Error {str(e)}")
        
        # Crear y ejecutar threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=crear_articulos, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Esperar a que todos los threads terminen
        for thread in threads:
            thread.join()
        
        # Verificaciones
        print(f"\n{'='*60}")
        print(f"RESULTADOS DEL TEST DE THREAD-SAFETY")
        print(f"{'='*60}")
        print(f"Threads ejecutados: {num_threads}")
        print(f"Artículos por thread: {articulos_por_thread}")
        print(f"Total esperado: {total_esperado}")
        print(f"Artículos creados: {len(articulos_creados)}")
        print(f"Errores: {len(errores)}")
        
        # Refrescar ubicación desde la BD
        self.ubicacion.refresh_from_db()
        capacidad_usada = 1000 - self.ubicacion.capacidad_disponible
        
        print(f"Capacidad inicial: 1000")
        print(f"Capacidad disponible: {self.ubicacion.capacidad_disponible}")
        print(f"Capacidad usada: {capacidad_usada}")
        
        # Verificar artículos en BD
        articulos_en_bd = Articulo.objects.filter(ubicacion=self.ubicacion).count()
        print(f"Artículos en BD: {articulos_en_bd}")
        print(f"{'='*60}\n")
        
        # Imprimir errores si los hay
        if errores:
            print("\nERRORES ENCONTRADOS:")
            for error in errores[:10]:  # Mostrar solo primeros 10
                print(f"  - {error}")
            if len(errores) > 10:
                print(f"  ... y {len(errores) - 10} errores más")
        
        # ASSERTIONS CRÍTICOS
        # 1. El número de artículos creados debe coincidir con los artículos en BD
        self.assertEqual(
            len(articulos_creados), 
            articulos_en_bd,
            "El número de artículos creados debe coincidir con los artículos en BD"
        )
        
        # 2. La capacidad usada debe coincidir con el número de artículos
        self.assertEqual(
            capacidad_usada,
            articulos_en_bd,
            f"La capacidad usada ({capacidad_usada}) debe coincidir con artículos en BD ({articulos_en_bd})"
        )
        
        # 3. Todos los artículos esperados deben haberse creado
        self.assertEqual(
            articulos_en_bd,
            total_esperado,
            f"Se esperaban {total_esperado} artículos, pero se crearon {articulos_en_bd}"
        )
        
        # 4. No debe haber errores
        self.assertEqual(
            len(errores),
            0,
            f"No debería haber errores, pero se encontraron {len(errores)}"
        )
    
    def test_ocupar_espacio_sin_capacidad(self):
        """
        Test que verifica que ocupar_espacio() retorna False cuando no hay capacidad
        """
        # Reducir capacidad a 5
        self.ubicacion.capacidad_disponible = 5
        self.ubicacion.save()
        
        # Intentar ocupar 10 espacios (más de lo disponible)
        resultado = self.ubicacion.ocupar_espacio(cantidad=10)
        
        # Debe retornar False
        self.assertFalse(resultado, "Debe retornar False cuando no hay capacidad suficiente")
        
        # Capacidad debe seguir siendo 5
        self.ubicacion.refresh_from_db()
        self.assertEqual(self.ubicacion.capacidad_disponible, 5, "La capacidad no debe cambiar")
    
    def test_ocupar_espacio_exacto(self):
        """
        Test que verifica que se puede ocupar exactamente la capacidad disponible
        """
        # Configurar capacidad a 10
        self.ubicacion.capacidad_disponible = 10
        self.ubicacion.save()
        
        # Ocupar exactamente 10 espacios
        resultado = self.ubicacion.ocupar_espacio(cantidad=10)
        
        # Debe retornar True
        self.assertTrue(resultado, "Debe retornar True cuando la cantidad es exacta")
        
        # Capacidad debe ser 0
        self.ubicacion.refresh_from_db()
        self.assertEqual(self.ubicacion.capacidad_disponible, 0, "La capacidad debe ser 0")
        
        # Intentar ocupar 1 espacio más debe fallar
        resultado2 = self.ubicacion.ocupar_espacio(cantidad=1)
        self.assertFalse(resultado2, "No debe poder ocupar cuando capacidad es 0")
