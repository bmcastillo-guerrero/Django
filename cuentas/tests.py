"""Pruebas de la app cuentas: sesión, autenticación, roles y permisos.

Cubre el indicador 5 de la Unidad 2 (Gestión de Sesiones y Autenticación)
y buena parte del indicador 2 (Django Admin) y 4 (seguridad del backend).
"""

from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario
from .roles import GRUPO_ADMINISTRADORES, MAPA_ROL_GRUPO


def asignar_rol(usuario, rol):
    """Asigna un rol al perfil y sincroniza el grupo de permisos de Django."""
    perfil = usuario.perfil
    perfil.rol = rol
    perfil.save(update_fields=['rol'])
    grupo = Group.objects.filter(name=MAPA_ROL_GRUPO[rol]).first()
    if grupo is not None:
        usuario.groups.clear()
        usuario.groups.add(grupo)
    return perfil


class BaseCuentas(TestCase):
    """Crea las tres cuentas con roles distintos para reutilizarlas en las pruebas."""

    def setUp(self):
        self.admin = User.objects.create_user(
            'ana', email='ana@ejemplo.cl', password='Administrador2026',
        )
        asignar_rol(self.admin, PerfilUsuario.ADMINISTRADOR)
        self.bodeguero = User.objects.create_user(
            'beto', email='beto@ejemplo.cl', password='Bodeguero2026',
        )
        asignar_rol(self.bodeguero, PerfilUsuario.BODEGUERO)
        self.vendedor = User.objects.create_user(
            'carla', email='carla@ejemplo.cl', password='Vendedor2026',
        )
        asignar_rol(self.vendedor, PerfilUsuario.VENDEDOR)


class PerfilTests(BaseCuentas):
    """Indicador 5: la señal crea el perfil y los helpers resuelven el rol."""

    def test_la_senal_crea_el_perfil_automaticamente(self):
        nuevo = User.objects.create_user('dani', password='Vendedor2026')
        self.assertTrue(PerfilUsuario.objects.filter(usuario=nuevo).exists())
        self.assertEqual(nuevo.perfil.rol, PerfilUsuario.VENDEDOR)

    def test_rol_por_defecto_es_vendedor(self):
        self.assertEqual(PerfilUsuario.objects.get(usuario=self.vendedor).rol, 'VENDEDOR')

    def test_ayudas_de_perfil_devuelven_true_segun_rol(self):
        from .permisos import es_administrador, es_bodeguero, es_vendedor

        self.assertTrue(es_administrador(self.admin))
        self.assertTrue(es_bodeguero(self.bodeguero))
        self.assertTrue(es_vendedor(self.vendedor))
        self.assertFalse(es_bodeguero(self.admin))

    def test_nombre_completo_cae_al_usuario_si_no_hay_nombre(self):
        self.assertEqual(self.vendedor.perfil.nombre_completo, 'carla')

    def test_iniciales_se_calculan_del_nombre(self):
        self.assertEqual(self.admin.perfil.iniciales, 'AN')

    def test_etiqueta_de_rol_es_legible(self):
        from .permisos import etiqueta_rol

        self.assertEqual(etiqueta_rol(self.bodeguero), 'Bodeguero')


class AutenticacionTests(BaseCuentas):
    """Indicador 5: inicio y cierre de sesión con la vista nativa de Django."""

    def test_ingresar_muestra_el_formulario(self):
        respuesta = self.client.get(reverse('login'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Iniciar sesión')

    def test_credenciales_validas_crean_sesion(self):
        respuesta = self.client.post(
            reverse('login'), {'username': 'ana', 'password': 'Administrador2026'}
        )
        self.assertRedirects(respuesta, reverse('dashboard'))

    def test_contrasena_incorrecta_no_crea_sesion(self):
        respuesta = self.client.post(
            reverse('login'), {'username': 'ana', 'password': 'incorrecta'}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(response_has_session(self))

    def test_registro_crea_cuenta_con_rol_minimo(self):
        respuesta = self.client.post(reverse('registro'), {
            'username': 'nueva',
            'nombre': 'Nueva Vendedora',
            'email': 'nueva@ejemplo.cl',
            'rol': PerfilUsuario.ADMINISTRADOR,
            'password1': 'VendedorSeguro2026',
            'password2': 'VendedorSeguro2026',
        })
        self.assertRedirects(respuesta, reverse('perfil'))
        # aunque se pidió administrador, el sistema entrega siempre el rol más bajo
        self.assertEqual(User.objects.get(username='nueva').perfil.rol, PerfilUsuario.VENDEDOR)

    def test_registro_rechaza_correo_duplicado(self):
        respuesta = self.client.post(reverse('registro'), {
            'username': 'otro', 'nombre': 'Otro Usuario', 'email': 'ANA@ejemplo.cl',
            'rol': PerfilUsuario.VENDEDOR,
            'password1': 'VendedorSeguro2026', 'password2': 'VendedorSeguro2026',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username='otro').exists())

    def test_cerrar_sesion_solo_acepta_post(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('logout'))
        self.assertEqual(respuesta.status_code, 405)

    def test_cerrar_sesion_destruye_la_sesion(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('logout'))
        respuesta = self.client.get(reverse('dashboard'))
        self.assertRedirects(respuesta, f"{reverse('login')}?next={reverse('dashboard')}")


def response_has_session(caso):
    """Devuelve True si el cliente de prueba quedó con una sesión iniciada."""
    return '_auth_user_id' in caso.client.session


class ExpiracionSesionTests(BaseCuentas):
    """Indicador 5: la política de expiración por inactividad del middleware."""

    def test_una_peticion_registra_la_marca_de_actividad(self):
        self.client.force_login(self.admin)
        self.client.get(reverse('dashboard'))
        self.assertIn('ultima_actividad', self.client.session)

    def test_sesion_antigua_se_cierra_por_inactividad(self):
        from datetime import timedelta

        from django.utils import timezone

        self.client.force_login(self.admin)
        sesion = self.client.session
        # la sesion se firma con json por eso la marca viaja como texto iso 8601
        sesion['ultima_actividad'] = (
            timezone.now() - timedelta(hours=3)
        ).isoformat()
        sesion.save()
        respuesta = self.client.get(reverse('dashboard'))
        self.assertRedirects(respuesta, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_sesion_reciente_se_mantiene(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('dashboard'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('_auth_user_id', self.client.session)


class ControlAccesoTests(BaseCuentas):
    """Indicador 5 y 4: rutas protegidas y permisos según el perfil de rol."""

    def test_anonimo_es_redirigido_al_login(self):
        respuesta = self.client.get(reverse('dashboard'))
        self.assertRedirects(respuesta, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_vendedor_no_puede_crear_productos(self):
        self.client.force_login(self.vendedor)
        respuesta = self.client.get(reverse('crear_producto'))
        self.assertEqual(respuesta.status_code, 403)

    def test_bodeguero_puede_crear_productos(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.get(reverse('crear_producto'))
        self.assertEqual(respuesta.status_code, 200)

    def test_bodeguero_no_puede_eliminar_productos(self):
        from inventario.models import Categoria, Producto

        producto = Producto.objects.create(
            nombre='Prueba', sku='TES-0001-AA', precio=10, stock=1, stock_minimo=1,
            categoria=Categoria.objects.create(nombre='Varios'),
        )
        self.client.force_login(self.bodeguero)
        respuesta = self.client.get(reverse('eliminar_producto', args=[producto.pk]))
        self.assertEqual(respuesta.status_code, 403)

    def test_lista_de_cuentas_es_exclusiva_del_administrador(self):
        self.client.force_login(self.bodeguero)
        self.assertEqual(self.client.get(reverse('lista_usuarios')).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('lista_usuarios')).status_code, 200)

    def test_perfil_guarda_los_datos_de_la_cuenta(self):
        self.client.force_login(self.bodeguero)
        respuesta = self.client.post(reverse('perfil'), {
            'first_name': 'Beto', 'last_name': 'Bodeguero', 'email': 'beto@ejemplo.cl',
            'telefono': '+56 9 1111 2222',
        })
        # la vista usa el patron post redirect get para no volver a enviar el formulario
        self.assertRedirects(respuesta, reverse('perfil'))
        self.bodeguero.refresh_from_db()
        self.assertEqual(self.bodeguero.email, 'beto@ejemplo.cl')


class CommandCrearRolesTests(TestCase):
    """Indicador 2 y 5: el comando que crea grupos, permisos y cuentas demo."""

    def test_comando_crea_grupos_y_cuentas(self):
        from io import StringIO

        from django.core.management import call_command

        salida = StringIO()
        call_command('crear_roles', stdout=salida)
        self.assertTrue(Group.objects.filter(name=GRUPO_ADMINISTRADORES).exists())
        self.assertTrue(User.objects.filter(username='admin.demo').exists())
        self.assertEqual(
            User.objects.get(username='bodega.demo').perfil.rol, PerfilUsuario.BODEGUERO
        )

    def test_administrador_demo_es_staff_para_entrar_al_panel(self):
        from io import StringIO

        from django.core.management import call_command

        call_command('crear_roles', '--sin-usuarios', stdout=StringIO())
        call_command('crear_roles', stdout=StringIO())
        self.assertTrue(User.objects.get(username='admin.demo').is_staff)

    def test_bodeguero_tiene_permiso_ajustar_stock(self):
        from io import StringIO

        from django.core.management import call_command

        call_command('crear_roles', stdout=StringIO())
        bodeguero = User.objects.get(username='bodega.demo')
        self.assertIn('inventario.puede_ajustar_stock', bodeguero.get_all_permissions())

    def test_vendedor_no_tiene_permiso_ajustar_stock(self):
        from io import StringIO

        from django.core.management import call_command

        call_command('crear_roles', stdout=StringIO())
        vendedor = User.objects.get(username='ventas.demo')
        self.assertNotIn('inventario.puede_ajustar_stock', vendedor.get_all_permissions())


class AdminCuentasTests(BaseCuentas):
    """Indicador 2: el perfil aparece embebido dentro de la ficha del usuario."""

    def setUp(self):
        super().setUp()
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()

    def test_ficha_de_usuario_muestra_el_perfil_inline(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(
            reverse('admin:auth_user_change', args=[self.bodeguero.pk])
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Perfil de StockFlow')

    def test_changelist_de_perfiles_indica_el_grupo(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('admin:cuentas_perfilusuario_changelist'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Grupo Django')
