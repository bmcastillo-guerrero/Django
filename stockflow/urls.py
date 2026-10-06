# aqui importo las herramientas para registrar rutas y vistas genericas
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

# aqui importo las vistas de obtencion y refresco de tokens jwt
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# aqui importo mis vistas de error para responder con la identidad visual de la aplicacion
from .errores import error_403, error_404, error_500

# aqui defino las rutas raiz del proyecto
urlpatterns = [
    # aqui redirijo la peticion del favicon al archivo estatico para evitar errores 404
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),

    # aqui conecto la ruta del panel de administracion nativo
    path('admin/', admin.site.urls),

    # aqui conecto los endpoints de autenticacion jwt stateless
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # aqui conecto los endpoints versionados v1 de la api restful de inventario
    path('api/v1/', include('inventario.api_urls')),

    # aqui conecto las rutas del modulo de cuentas antes que inventario para no perder el login
    path('', include('cuentas.urls')),
    # aqui conecto las rutas de la aplicacion inventario al inicio del sitio
    path('', include('inventario.urls')),
]

# aqui defino las paginas de error del proyecto para reemplazar las pantallas grises de django
handler403 = 'stockflow.errores.error_403'
handler404 = 'stockflow.errores.error_404'
handler500 = 'stockflow.errores.error_500'
