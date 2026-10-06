# aqui importo path y el router predeterminado de django rest framework
from django.urls import path
from rest_framework.routers import DefaultRouter

# aqui importo los viewsets y vistas de la api de inventario
from .api_views import (
    CategoriaViewSet,
    ProductoViewSet,
    MovimientoStockViewSet,
    CatalogoProveedorView,
)

# aqui instancio el router por defecto que genera automaticamente las rutas restful en plural
router = DefaultRouter()
# aqui registro las colecciones de categorias productos y movimientos
router.register(r'categorias', CategoriaViewSet, basename='api-categoria')
router.register(r'productos', ProductoViewSet, basename='api-producto')
router.register(r'movimientos', MovimientoStockViewSet, basename='api-movimiento')

# aqui exporto las rutas del router sumando el endpoint de la api externa
urlpatterns = [
    # aqui expongo el endpoint REST que consulta la API externa de proveedores mayoristas
    path('proveedores/', CatalogoProveedorView.as_view(), name='api-proveedores'),
] + router.urls
