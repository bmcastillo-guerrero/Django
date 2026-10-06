# aqui importo la funcion path para mapear urls con vistas
from django.urls import path

# aqui importo las vistas basadas en clases del modulo de inventario
from . import views

# aqui defino las rutas de navegacion de la aplicacion de inventario
urlpatterns = [
    # aqui conecto la raiz con la vista del panel de control y sus metricas
    path('', views.VistaDashboard.as_view(), name='dashboard'),

    # aqui conecto el catalogo de productos con filtros orden y paginacion
    path('productos/', views.VistaListaProductos.as_view(), name='lista_productos'),
    # aqui conecto la vista interactiva desacoplada que consume la api restful mediante javascript fetch
    path('catalogo-api/', views.VistaCatalogoApi.as_view(), name='catalogo_api'),
    # aqui conecto la accion masiva de activar o desactivar productos del catalogo
    path('productos/accion-masiva/', views.VistaAccionMasiva.as_view(), name='accion_masiva'),
    # aqui conecto la ruta para el formulario de creacion de producto
    path('productos/nuevo/', views.VistaCrearProducto.as_view(), name='crear_producto'),
    # aqui conecto el detalle de un producto individual recibiendo su clave primaria
    path('productos/<int:pk>/', views.VistaDetalleProducto.as_view(), name='detalle_producto'),
    # aqui conecto la edicion del producto mediante su clave primaria
    path('productos/<int:pk>/editar/', views.VistaEditarProducto.as_view(), name='editar_producto'),
    # aqui conecto la confirmacion de eliminacion del producto
    path(
        'productos/<int:pk>/eliminar/',
        views.VistaEliminarProducto.as_view(),
        name='eliminar_producto',
    ),
    # aqui conecto el registro de entradas y salidas sobre un producto concreto
    path(
        'productos/<int:pk>/movimientos/',
        views.VistaRegistrarMovimiento.as_view(),
        name='registrar_movimiento',
    ),
    # aqui conecto el ajuste directo de stock para quien tenga el permiso especifico
    path(
        'productos/<int:pk>/ajuste/',
        views.VistaAjustarStock.as_view(),
        name='ajustar_stock',
    ),

    # aqui conecto la coleccion global del historial de movimientos con sus filtros
    path(
        'movimientos/',
        views.VistaHistorialMovimientos.as_view(),
        name='historial_movimientos',
    ),

    # aqui conecto la coleccion de categorias con su conteo de productos
    path('categorias/', views.VistaListaCategorias.as_view(), name='lista_categorias'),
    # aqui conecto el alta de una categoria nueva
    path('categorias/nueva/', views.VistaCrearCategoria.as_view(), name='crear_categoria'),
    # aqui conecto la edicion de una categoria existente
    path(
        'categorias/<int:pk>/editar/',
        views.VistaEditarCategoria.as_view(),
        name='editar_categoria',
    ),
    # aqui conecto la eliminacion de una categoria que ya no tenga productos
    path(
        'categorias/<int:pk>/eliminar/',
        views.VistaEliminarCategoria.as_view(),
        name='eliminar_categoria',
    ),
]
