"""Pruebas de la app inventario: modelos, servicios, selectores, CRUD y admin.

Cubre los indicadores 1, 2, 3 y 4 de la Unidad 2.
"""

from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from cuentas.models import PerfilUsuario
from cuentas.roles import MAPA_ROL_GRUPO
from inventario.excepciones import (
    MovimientoInvalidoError,
    ProductoInactivoError,
    StockInsuficienteError,
)
from inventario.models import Categoria, MovimientoStock, Producto
from inventario.selectores import historial_movimientos, metricas_dashboard, productos_filtrados
from inventario.servicios import (
    activar_productos,
    ajustar_stock,
    desactivar_productos,
    registrar_movimiento,
)


def asignar_rol(usuario, rol):
    """Asigna el rol al perfil y sincroniza el grupo de permisos de Django."""
    perfil = usuario.perfil
    perfil.rol = rol
    perfil.save(update_fields=['rol'])
    grupo = Group.objects.filter(name=MAPA_ROL_GRUPO[rol]).first()
    if grupo is not None:
        usuario.groups.clear()
        usuario.groups.add(grupo)
    return usuario


class BaseInventario(TestCase):
    """Datos compartidos: una categoría, un producto y las cuentas de cada rol."""

    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Abarrotes')
        self.producto = Producto.objects.create(
            nombre='Arroz Grado 1',
            sku='ABE-1001-AB',
            categoria=self.categoria,
            precio=Decimal('1250.00'),
            stock=10,
            stock_minimo=5,
        )
        self.admin = asignar_rol(
            User.objects.create_user('ana', password='Administrador2026'),
            PerfilUsuario.ADMINISTRADOR,
        )
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()
        self.bodeguero = asignar_rol(
            User.objects.create_user('beto', password='Bodeguero2026'),
            PerfilUsuario.BODEGUERO,
        )
        self.vendedor = asignar_rol(
            User.objects.create_user('carla', password='Vendedor2026'),
            PerfilUsuario.VENDEDOR,
        )


# =============================================================================
# Indicador 1 · Modelos y configuración de base de datos
# =============================================================================
class ModelosTests(BaseInventario):
    def test_str_producto_incluye_sku(self):
        self.assertIn('ABE-1001-AB', str(self.producto))

    def test_necesita_reposicion_cuando_stock_bajo(self):
        self.producto.stock = 3
        self.assertTrue(self.producto.necesita_reposicion)

    def test_valor_inventario_multiplica_precio_por_stock(self):
        self.assertEqual(self.producto.valor_inventario, Decimal('1250.00') * 10)

    def test_total_productos_por_categoria(self):
        Producto.objects.create(
            nombre='Fideos', sku='ABE-1002-AB', categoria=self.categoria,
            precio=Decimal('990'),
        )
        self.assertEqual(self.categoria.total_productos, 2)

    def test_sku_con_formato_invalido_es_rechazado(self):
        from django.core.exceptions import ValidationError

        producto = Producto(
            nombre='Mal formado', sku='sku con espacios',
            categoria=self.categoria, precio=Decimal('100'),
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_categoria_con_productos_no_se_puede_borrar(self):
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_borrar_producto_arrastra_sus_movimientos(self):
        MovimientoStock.objects.create(
            producto=self.producto, tipo='ENTRADA', cantidad=5,
        )
        self.producto.delete()
        self.assertEqual(MovimientoStock.objects.count(), 0)

    def test_valor_movimiento_calcula_precio_por_cantidad(self):
        movimiento = MovimientoStock.objects.create(
            producto=self.producto, tipo='SALIDA', cantidad=2,
        )
        self.assertEqual(movimiento.valor_movimiento, Decimal('2500.00'))
        self.assertEqual(movimiento.suma_stock, -2)


# =============================================================================
# Indicador 4 · Capa de servicios con transacciones
# =============================================================================
class ServiciosTests(BaseInventario):
    def test_entrada_aumenta_stock_y_registra_usuario(self):
        movimiento = registrar_movimiento(
            producto=self.producto, tipo='ENTRADA', cantidad=15,
            observacion='Compra a proveedor', usuario=self.bodeguero,
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 25)
        self.assertEqual(movimiento.registrado_por, self.bodeguero)

    def test_salida_disminuye_stock(self):
        registrar_movimiento(
            producto=self.producto, tipo='SALIDA', cantidad=4, usuario=self.bodeguero,
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 6)

    def test_salida_mayor_al_stock_lanza_stock_insuficiente(self):
        with self.assertRaises(StockInsuficienteError):
            registrar_movimiento(
                producto=self.producto, tipo='SALIDA', cantidad=99, usuario=self.bodeguero,
            )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_error_de_negocio_no_deja_movimiento_ni_stock_negativo(self):
        with self.assertRaises(StockInsuficienteError):
            registrar_movimiento(
                producto=self.producto, tipo='SALIDA', cantidad=999, usuario=self.bodeguero,
            )
        self.assertFalse(MovimientoStock.objects.exists())
        self.assertGreater(Producto.objects.get(pk=self.producto.pk).stock, 0)

    def test_movimiento_sobre_producto_inactivo_es_rechazado(self):
        desactivar_productos([self.producto], usuario=self.bodeguero)
        with self.assertRaises(ProductoInactivoError):
            registrar_movimiento(
                producto=self.producto, tipo='ENTRADA', cantidad=1, usuario=self.bodeguero,
            )

    def test_cantidad_cero_o_negativa_es_rechazada(self):
        with self.assertRaises(MovimientoInvalidoError):
            registrar_movimiento(
                producto=self.producto, tipo='ENTRADA', cantidad=0, usuario=self.bodeguero,
            )

    def test_tipo_invalido_es_rechazado(self):
        with self.assertRaises(MovimientoInvalidoError):
            registrar_movimiento(
                producto=self.producto, tipo='DONACION', cantidad=1, usuario=self.bodeguero,
            )

    def test_ajustar_stock_no_genera_movimiento(self):
        ajustar_stock(self.producto, 42, usuario=self.bodeguero)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 42)
        self.assertEqual(MovimientoStock.objects.count(), 0)

    def test_ajustar_stock_negativo_es_rechazado(self):
        with self.assertRaises(MovimientoInvalidoError):
            ajustar_stock(self.producto, -5, usuario=self.bodeguero)

    def test_accion_masiva_desactiva_y_reactiva(self):
        otro = Producto.objects.create(
            nombre='Fideos', sku='ABE-1002-AB', categoria=self.categoria,
            precio=Decimal('990'), stock=30,
        )
        self.assertEqual(desactivar_productos([self.producto, otro]), 2)
        self.assertEqual(Producto.objects.filter(activo=True).count(), 0)
        self.assertEqual(activar_productos([self.producto, otro]), 2)
        self.assertEqual(Producto.objects.filter(activo=True).count(), 2)


# =============================================================================
# Indicador 4 · Selectores de solo lectura
# =============================================================================
class SelectoresTests(BaseInventario):
    def test_metricas_suman_el_valor_del_inventario(self):
        Producto.objects.create(
            nombre='Fideos', sku='ABE-1002-AB', categoria=self.categoria,
            precio=Decimal('500'), stock=4,
        )
        metricas = metricas_dashboard()
        self.assertEqual(metricas['total_productos'], 2)
        self.assertEqual(metricas['total_unidades'], 14)
        self.assertEqual(metricas['valor_inventario'], Decimal('14500.00'))

    def test_metricas_excluyen_productos_inactivos(self):
        desactivar_productos([self.producto])
        self.assertEqual(metricas_dashboard()['total_productos'], 0)

    def test_busqueda_por_nombre_o_sku(self):
        Producto.objects.create(
            nombre='Fideos Espirales', sku='ABE-1002-AB', categoria=self.categoria,
            precio=Decimal('990'), stock=8,
        )
        self.assertEqual(productos_filtrados('espirales').count(), 1)
        self.assertEqual(productos_filtrados('ABE-1002').count(), 1)
        self.assertEqual(productos_filtrados('inexistente').count(), 0)

    def test_ordenamiento_con_lista_blanca(self):
        Producto.objects.create(
            nombre='Zanahoria', sku='ABE-1003-AB', categoria=self.categoria,
            precio=Decimal('300'), stock=7,
        )
        primero = productos_filtrados(orden='nombre').first()
        self.assertEqual(primero.nombre, 'Arroz Grado 1')
        primero_precio = productos_filtrados(orden='precio_asc').first()
        self.assertEqual(primero_precio.sku, 'ABE-1003-AB')

    def test_orden_invalido_cae_al_orden_por_defecto(self):
        self.assertEqual(productos_filtrados(orden='drop table').count(), 1)

    def test_historial_filtra_por_tipo_y_texto(self):
        registrar_movimiento(
            producto=self.producto, tipo='ENTRADA', cantidad=5,
            observacion='Proveedor SUR', usuario=self.bodeguero,
        )
        registrar_movimiento(
            producto=self.producto, tipo='SALIDA', cantidad=2,
            observacion='Venta mostrador', usuario=self.bodeguero,
        )
        self.assertEqual(historial_movimientos(tipo='ENTRADA').count(), 1)
        self.assertEqual(historial_movimientos(query='SUR').count(), 1)
        self.assertEqual(historial_movimientos(query='ventana').count(), 0)


# =============================================================================
# Indicador 3 · Formularios y validaciones rigurosas
# =============================================================================
class FormulariosTests(BaseInventario):
    def datos_producto(self, **cambios):
        base = {
            'nombre': 'Aceite Vegetal', 'sku': 'ABE-2001-AB',
            'categoria': self.categoria.pk, 'precio': '3500',
            'stock': '20', 'stock_minimo': '4', 'unidad_medida': 'UN',
        }
        base.update(cambios)
        return base

    def test_sku_se_normaliza_a_mayusculas(self):
        from inventario.forms import ProductoForm

        formulario = ProductoForm(data=self.datos_producto(sku='abe-2001-ab'))
        self.assertTrue(formulario.is_valid())
        self.assertEqual(formulario.cleaned_data['sku'], 'ABE-2001-AB')

    def test_sku_duplicado_es_rechazado(self):
        from inventario.forms import ProductoForm

        formulario = ProductoForm(data=self.datos_producto(sku='ABE-1001-AB'))
        self.assertFalse(formulario.is_valid())
        self.assertIn('sku', formulario.errors)

    def test_precio_cero_es_rechazado(self):
        from inventario.forms import ProductoForm

        formulario = ProductoForm(data=self.datos_producto(precio='0'))
        self.assertFalse(formulario.is_valid())
        self.assertIn('precio', formulario.errors)

    def test_stock_minimo_mayor_al_stock_es_rechazado(self):
        from inventario.forms import ProductoForm

        formulario = ProductoForm(data=self.datos_producto(stock='3', stock_minimo='10'))
        self.assertFalse(formulario.is_valid())
        self.assertIn('stock_minimo', formulario.errors)

    def test_sin_permiso_de_precios_el_campo_va_bloqueado(self):
        from inventario.forms import ProductoForm

        formulario = ProductoForm(data=self.datos_producto(), usuario=self.vendedor)
        self.assertTrue(formulario.is_valid())
        self.assertIn('disabled', formulario.fields['precio'].widget.attrs)

    def test_nombre_de_categoria_repetido_es_rechazado(self):
        from inventario.forms import CategoriaForm

        formulario = CategoriaForm(data={'nombre': 'abarrotes'})
        self.assertFalse(formulario.is_valid())
        self.assertIn('nombre', formulario.errors)

    def test_salida_mayor_al_stock_es_rechazada_en_el_formulario(self):
        from inventario.forms import MovimientoForm

        formulario = MovimientoForm(
            data={'tipo': 'SALIDA', 'cantidad': '99', 'observacion': ''},
            producto=self.producto,
        )
        self.assertFalse(formulario.is_valid())

    def test_movimiento_sobre_producto_inactivo_es_rechazado(self):
        from inventario.forms import MovimientoForm

        desactivar_productos([self.producto])
        formulario = MovimientoForm(
            data={'tipo': 'ENTRADA', 'cantidad': '1', 'observacion': ''},
            producto=Producto.objects.get(pk=self.producto.pk),
        )
        self.assertFalse(formulario.is_valid())


# =============================================================================
# Indicador 3 · Operaciones CRUD sobre las colecciones
# =============================================================================
class CrudProductosTests(BaseInventario):
    def test_dashboard_responde_con_metricas(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.get(reverse('dashboard'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Panel de inventario')
        self.assertEqual(respuesta.context['total_productos'], 1)

    def test_lista_filtra_por_busqueda_y_avisa_si_no_encuentra(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.get(reverse('lista_productos'), {'q': 'arroz'})
        self.assertContains(respuesta, 'Arroz Grado 1')
        vacia = self.client.get(reverse('lista_productos'), {'q': 'inexistente'})
        self.assertContains(vacia, 'No se encontraron productos')

    def test_lista_ordena_con_el_criterio_recibido(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.get(reverse('lista_productos'), {'orden': 'nombre'})
        self.assertEqual(respuesta.context['orden'], 'nombre')

    def test_crear_producto_registra_al_usuario_autor(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.post(reverse('crear_producto'), {
            'nombre': 'Aceite Vegetal', 'sku': 'abe-2001-ab', 'categoria': self.categoria.pk,
            'precio': '3500', 'stock': '20', 'stock_minimo': '4',
            'unidad_medida': 'UN', 'activo': 'on',
        })
        self.assertRedirects(respuesta, reverse('lista_productos'))
        creado = Producto.objects.get(sku='ABE-2001-AB')
        self.assertEqual(creado.creado_por, self.bodeguero)

    def test_editar_producto_actualiza_el_catalogo(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.post(
            reverse('editar_producto', args=[self.producto.pk]),
            {'nombre': 'Arroz Grado 2', 'sku': 'ABE-1001-AB', 'categoria': self.categoria.pk,
             'precio': '1300', 'stock': '10', 'stock_minimo': '5',
             'unidad_medida': 'UN', 'activo': 'on'},
        )
        self.assertRedirects(respuesta, reverse('lista_productos'))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, 'Arroz Grado 2')

    def test_eliminar_producto_borra_su_historial(self):
        MovimientoStock.objects.create(
            producto=self.producto, tipo='ENTRADA', cantidad=4,
        )
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse('eliminar_producto', args=[self.producto.pk])
        )
        self.assertRedirects(respuesta, reverse('lista_productos'))
        self.assertFalse(Producto.objects.filter(pk=self.producto.pk).exists())
        self.assertEqual(MovimientoStock.objects.count(), 0)

    def test_sku_duplicado_no_crea_un_segundo_producto(self):
        self.client.force_login(self.bodeguero)
        self.client.post(reverse('crear_producto'), {
            'nombre': 'Repetido', 'sku': 'ABE-1001-AB', 'categoria': self.categoria.pk,
            'precio': '100', 'stock': '1', 'stock_minimo': '1', 'unidad_medida': 'UN',
        })
        self.assertEqual(Producto.objects.filter(sku='ABE-1001-AB').count(), 1)

    def test_detalle_de_producto_inexistente_devuelve_404(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.get(reverse('detalle_producto', args=[999999]))
        self.assertEqual(respuesta.status_code, 404)


class MovimientosPorVistaTests(BaseInventario):
    def test_entrada_aumenta_el_stock(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.post(
            reverse('registrar_movimiento', args=[self.producto.pk]),
            {'tipo': 'ENTRADA', 'cantidad': '8', 'observacion': 'Reposición'},
        )
        self.assertRedirects(
            respuesta, reverse('detalle_producto', args=[self.producto.pk])
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 18)

    def test_salida_disminuye_el_stock(self):
        self.client.force_login(self.bodeguero)
        self.client.post(
            reverse('registrar_movimiento', args=[self.producto.pk]),
            {'tipo': 'SALIDA', 'cantidad': '5', 'observacion': ''},
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_salida_mayor_al_stock_no_modifica_el_stock(self):
        self.client.force_login(self.bodeguero)
        self.client.post(
            reverse('registrar_movimiento', args=[self.producto.pk]),
            {'tipo': 'SALIDA', 'cantidad': '99', 'observacion': ''},
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_vendedor_no_puede_registrar_movimientos(self):
        self.client.force_login(self.vendedor)
        respuesta = self.client.post(
            reverse('registrar_movimiento', args=[self.producto.pk]),
            {'tipo': 'ENTRADA', 'cantidad': '8', 'observacion': ''},
        )
        self.assertEqual(respuesta.status_code, 403)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_ajuste_directo_exige_el_permiso_especifico(self):
        self.client.force_login(self.vendedor)
        respuesta = self.client.post(
            reverse('ajustar_stock', args=[self.producto.pk]), {'nuevo_stock': '99'}
        )
        self.assertRedirects(respuesta, reverse('dashboard'))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_ajuste_directo_cambia_el_stock_para_quien_tiene_permiso(self):
        call_command('crear_roles', stdout=StringIO())
        bodeguero_demo = User.objects.get(username='bodega.demo')
        self.client.force_login(bodeguero_demo)
        respuesta = self.client.post(
            reverse('ajustar_stock', args=[self.producto.pk]),
            {'nuevo_stock': '77', 'motivo': 'Conteo físico'},
        )
        self.assertRedirects(
            respuesta, reverse('detalle_producto', args=[self.producto.pk])
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 77)


class AccionMasivaTests(BaseInventario):
    def setUp(self):
        super().setUp()
        self.otro = Producto.objects.create(
            nombre='Fideos', sku='ABE-1002-AB', categoria=self.categoria,
            precio=Decimal('990'), stock=30,
        )

    def test_accion_masiva_desactiva_los_seleccionados(self):
        self.client.force_login(self.bodeguero)
        self.client.post(reverse('accion_masiva'), {
            'accion': 'desactivar',
            'productos': [str(self.producto.pk), str(self.otro.pk)],
        })
        self.assertEqual(Producto.objects.filter(activo=True).count(), 0)

    def test_accion_masiva_reactiva_los_seleccionados(self):
        desactivar_productos([self.producto, self.otro])
        self.client.force_login(self.bodeguero)
        self.client.post(reverse('accion_masiva'), {
            'accion': 'activar',
            'productos': [str(self.producto.pk), str(self.otro.pk)],
        })
        self.assertEqual(Producto.objects.filter(activo=True).count(), 2)

    def test_sin_seleccion_no_hace_nada(self):
        self.client.force_login(self.bodeguero)
        self.client.post(reverse('accion_masiva'), {'accion': 'desactivar', 'productos': []})
        self.assertEqual(Producto.objects.filter(activo=True).count(), 2)


class ColeccionesTests(BaseInventario):
    def test_historial_de_movimientos_filtra_por_tipo(self):
        registrar_movimiento(
            producto=self.producto, tipo='ENTRADA', cantidad=5, usuario=self.bodeguero,
        )
        self.client.force_login(self.vendedor)
        respuesta = self.client.get(reverse('historial_movimientos'), {'tipo': 'ENTRADA'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'ENTRADA')
        self.assertEqual(len(respuesta.context['movimientos']), 1)

    def test_lista_de_categorias_muestra_el_conteo(self):
        self.client.force_login(self.vendedor)
        respuesta = self.client.get(reverse('lista_categorias'))
        self.assertContains(respuesta, 'Abarrotes')
        self.assertEqual(respuesta.context['categorias'][0].total_productos, 1)

    def test_crear_categoria_normaliza_el_nombre(self):
        self.client.force_login(self.bodeguero)
        self.client.post(reverse('crear_categoria'), {'nombre': 'bebidas', 'descripcion': 'Gaseosas'})
        self.assertTrue(Categoria.objects.filter(nombre='Bebidas').exists())

    def test_categoria_protegida_no_se_puede_eliminar(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse('eliminar_categoria', args=[self.categoria.pk])
        )
        self.assertRedirects(respuesta, reverse('lista_categorias'))
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_categoria_vacia_si_se_puede_eliminar(self):
        categoria = Categoria.objects.create(nombre='Limpieza')
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse('eliminar_categoria', args=[categoria.pk]))
        self.assertRedirects(respuesta, reverse('lista_categorias'))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())


# =============================================================================
# Indicador 2 · Django Admin
# =============================================================================
class AdminInventarioTests(BaseInventario):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_changelist_de_productos_carga(self):
        respuesta = self.client.get(reverse('admin:inventario_producto_changelist'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Estado de stock')

    def test_filtro_por_stock_bajo(self):
        # bajo el stock del producto base para que quede por debajo de su minimo de 5
        self.producto.stock = 3
        self.producto.save(update_fields=['stock'])
        Producto.objects.create(
            nombre='Fideos', sku='ABE-1002-AB', categoria=self.categoria,
            precio=Decimal('990'), stock=30, stock_minimo=5,
        )
        respuesta = self.client.get(
            reverse('admin:inventario_producto_changelist'),
            {'stock_bajo': 'por_reponer'},
        )
        self.assertEqual(
            [p.pk for p in respuesta.context['cl'].result_list], [self.producto.pk]
        )

    def test_accion_masiva_descontinuar(self):
        # el nombre interno de la accion es accion_desactivar segun el decorador del panel
        self.client.post(reverse('admin:inventario_producto_changelist'), {
            'action': 'accion_desactivar',
            '_selected_action': [str(self.producto.pk)],
        })
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)

    def test_accion_masiva_reposicion_automatica(self):
        self.client.post(reverse('admin:inventario_producto_changelist'), {
            'action': 'accion_entrada_stock',
            '_selected_action': [str(self.producto.pk)],
        })
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 20)

    def test_inline_de_movimientos_en_la_ficha_del_producto(self):
        registrar_movimiento(
            producto=self.producto, tipo='ENTRADA', cantidad=5, usuario=self.bodeguero,
        )
        respuesta = self.client.get(
            reverse('admin:inventario_producto_change', args=[self.producto.pk])
        )
        self.assertContains(respuesta, 'Historial de movimientos de este producto')

    def test_changelist_de_movimientos_carga_con_historial_por_fecha(self):
        registrar_movimiento(
            producto=self.producto, tipo='SALIDA', cantidad=2, usuario=self.bodeguero,
        )
        respuesta = self.client.get(
            reverse('admin:inventario_movimientostock_changelist')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Valor del movimiento')

    def test_el_admin_ignora_a_los_usuarios_sin_permiso(self):
        from django.contrib.auth.models import User as U

        lector = U.objects.create_user('lector', password='Lector2026', is_staff=True)
        self.client.force_login(lector)
        respuesta = self.client.get(reverse('admin:inventario_producto_changelist'))
        self.assertEqual(respuesta.status_code, 403)
