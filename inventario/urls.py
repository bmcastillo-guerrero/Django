# aqui importo path para mapear urls con funciones de vista
from django.urls import path

# aqui importo el modulo de vistas de inventario
from . import views

# aqui defino las rutas de navegacion de la aplicacion
urlpatterns = [
    # aqui conecto la raiz con la vista del panel de control
    path('', views.dashboard, name='dashboard'),
    # aqui conecto la url de catalogo con filtros y buscador
    path('productos/', views.lista_productos, name='lista_productos'),
    # aqui conecto la ruta para el formulario de creacion de producto
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    # aqui conecto el detalle de un producto individual recibiendo su clave primaria
    path('productos/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    # aqui conecto la edicion del producto mediante su clave primaria
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    # aqui conecto la confirmacion de eliminacion del producto
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
]
