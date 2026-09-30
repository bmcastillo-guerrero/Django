# aqui importo la funcion path para mapear urls con vistas
from django.urls import path

# aqui importo las vistas de la aplicacion de cuentas
from . import views

# aqui defino las rutas del modulo de cuentas sesiones y roles
urlpatterns = [
    # aqui conecto la ruta de acceso con la vista nativa de login de django
    path(
        'ingresar/',
        views.VistaIniciarSesion.as_view(),
        name='login',
    ),
    # aqui conecto la ruta de salida que exige post y token csrf para evitar cierres forzosos
    path(
        'salir/',
        views.VistaCerrarSesion.as_view(),
        name='logout',
    ),
    # aqui conecto el alta publica de cuentas con la vista de registro
    path(
        'registro/',
        views.VistaRegistro.as_view(),
        name='registro',
    ),
    # aqui conecto la ficha del usuario conectado para ver y editar sus datos
    path(
        'perfil/',
        views.VistaPerfil.as_view(),
        name='perfil',
    ),
    # aqui conecto el listado de cuentas restringido solo a administradores
    path(
        'cuentas/',
        views.VistaListaUsuarios.as_view(),
        name='lista_usuarios',
    ),
]
