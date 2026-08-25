from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Categoria, MovimientoStock, Producto


class ModelTests(TestCase):
    """Prueba las propiedades y operaciones de los modelos."""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Abarrotes')
        self.producto = Producto.objects.create(
            nombre='Arroz Grado 1',
            sku='SKU-1001-AB',
            categoria=self.categoria,
            precio=Decimal('1250.00'),
            stock=10,
            stock_minimo=5,
        )

    def test_str_producto_incluye_sku(self):
        self.assertIn('SKU-1001-AB', str(self.producto))

    def test_necesita_reposicion_cuando_stock_bajo(self):
        self.producto.stock = 3
        self.assertTrue(self.producto.necesita_reposicion)

    def test_no_reposicion_con_stock_suficiente(self):
        self.producto.stock = 20
        self.assertFalse(self.producto.necesita_reposicion)

    def test_valor_inventario_multiplica_precio_por_stock(self):
        esperado = Decimal('1250.00') * 10
        self.assertEqual(self.producto.valor_inventario, esperado)

    def test_total_productos_por_categoria(self):
        Producto.objects.create(
            nombre='Fideos', sku='SKU-1002-AB',
            categoria=self.categoria, precio=Decimal('990'),
        )
        self.assertEqual(self.categoria.total_productos, 2)

    def test_movimiento_actualiza_historial(self):
        MovimientoStock.objects.create(
            producto=self.producto, tipo='ENTRADA', cantidad=15,
        )
        self.assertEqual(self.producto.movimientos.count(), 1)


class VistaTests(TestCase):
    """Prueba los flujos GET/POST de las vistas (controlador del MVC)."""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Bebidas')
        self.producto = Producto.objects.create(
            nombre='Gaseosa Cola 3LT',
            sku='SKU-2002-BB',
            categoria=self.categoria,
            precio=Decimal('2450'),
            stock=12,
            stock_minimo=6,
        )

    def test_dashboard_responde_y_muestra_metricas(self):
        respuesta = self.client.get(reverse('dashboard'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Panel de inventario')
        self.assertEqual(respuesta.context['total_productos'], 1)

    def test_lista_filtra_por_busqueda(self):
        respuesta = self.client.get(reverse('lista_productos'), {'q': 'cola'})
        self.assertContains(respuesta, 'Gaseosa Cola')

        respuesta = self.client.get(reverse('lista_productos'), {'q': 'inexistente'})
        self.assertContains(respuesta, 'No se encontraron productos')

    def test_crear_producto_via_post(self):
        datos = {
            'nombre': 'Agua Mineral 1LT',
            'sku': 'SKU-2003-BB',
            'categoria': self.categoria.pk,
            'precio': '900.00',
            'stock': '30',
            'stock_minimo': '5',
            'unidad_medida': 'UN',
            'activo': 'on',
        }
        respuesta = self.client.post(reverse('crear_producto'), datos)
        self.assertRedirects(respuesta, reverse('lista_productos'))
        self.assertTrue(Producto.objects.filter(sku='SKU-2003-BB').exists())

    def test_sku_duplicado_es_rechazado(self):
        datos = {
            'nombre': 'Producto Repetido',
            'sku': 'SKU-2002-BB',
            'categoria': self.categoria.pk,
            'precio': '100',
            'stock': '1',
            'stock_minimo': '1',
            'unidad_medida': 'UN',
        }
        respuesta = self.client.post(reverse('crear_producto'), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Producto.objects.filter(sku='SKU-2002-BB').count(), 1)

    def test_editar_producto_modifica_datos(self):
        datos = {
            'nombre': 'Gaseosa Cola 3LT Light',
            'sku': 'SKU-2002-BB',
            'categoria': self.categoria.pk,
            'precio': '2600',
            'stock': '12',
            'stock_minimo': '6',
            'unidad_medida': 'UN',
            'activo': 'on',
        }
        respuesta = self.client.post(
            reverse('editar_producto', args=[self.producto.pk]), datos
        )
        self.assertRedirects(respuesta, reverse('lista_productos'))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, 'Gaseosa Cola 3LT Light')

    def test_movimiento_entrada_aumenta_stock(self):
        respuesta = self.client.post(
            reverse('detalle_producto', args=[self.producto.pk]),
            {'tipo': 'ENTRADA', 'cantidad': '8', 'observacion': 'Reposición'},
        )
        self.assertRedirects(
            respuesta, reverse('detalle_producto', args=[self.producto.pk])
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 20)

    def test_movimiento_salida_disminuye_stock(self):
        self.client.post(
            reverse('detalle_producto', args=[self.producto.pk]),
            {'tipo': 'SALIDA', 'cantidad': '5', 'observacion': ''},
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)

    def test_salida_mayor_al_stock_es_rechazada(self):
        respuesta = self.client.post(
            reverse('detalle_producto', args=[self.producto.pk]),
            {'tipo': 'SALIDA', 'cantidad': '99', 'observacion': ''},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Solo hay 12 unidades disponibles')
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 12)

    def test_eliminar_producto_borra_movimientos(self):
        MovimientoStock.objects.create(
            producto=self.producto, tipo='ENTRADA', cantidad=4,
        )
        respuesta = self.client.post(
            reverse('eliminar_producto', args=[self.producto.pk])
        )
        self.assertRedirects(respuesta, reverse('lista_productos'))
        self.assertFalse(Producto.objects.filter(pk=self.producto.pk).exists())
        self.assertEqual(MovimientoStock.objects.count(), 0)
