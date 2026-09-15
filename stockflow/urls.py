# aqui importo las herramientas para registrar rutas y vistas genericas
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

# aqui defino las rutas raiz del proyecto
urlpatterns = [
    # aqui redirijo la peticion del favicon al archivo estatico para evitar errores 404
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),

    # aqui conecto la ruta del panel de administracion nativo
    path('admin/', admin.site.urls),

    # aqui conecto las rutas de la aplicacion inventario al inicio del sitio
    path('', include('inventario.urls')),
]
