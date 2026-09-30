# aqui importo el renderizador de django para devolver mis paginas de error con codigo correcto
from django.shortcuts import render
# aqui importo el logger del proyecto para dejar constancia de los errores controlados
import logging

# aqui creo el logger propio del modulo de errores
logger = logging.getLogger('stockflow.errores')


# aqui defino la vista que se muestra cuando el usuario no tiene permisos para la pagina
def error_403(request, exception=None):
    # aqui registro el intento de acceso denegado con su motivo
    logger.warning('Acceso denegado (403) a %s por %s', request.path, request.user)
    # aqui devuelvo la plantilla de error con el codigo 403 prohibido
    return render(request, 'errores/403.html', status=403)


# aqui defino la vista que se muestra cuando la direccion solicitada no existe
def error_404(request, exception=None):
    # aqui registro la direccion que no se encontro en el sistema
    logger.warning('Página no encontrada (404): %s', request.path)
    # aqui devuelvo la plantilla de error con el codigo 404 no encontrado
    return render(request, 'errores/404.html', status=404)


# aqui defino la vista que se muestra cuando el servidor falla de forma inesperada
def error_500(request):
    # aqui registro el fallo grave con la traza completa para poder diagnosticarlo
    logger.exception('Error interno del servidor (500) en %s', request.path)
    # aqui devuelvo la plantilla de error con el codigo 500 error interno
    return render(request, 'errores/500.html', status=500)
