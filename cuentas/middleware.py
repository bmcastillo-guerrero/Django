# aqui importo la clase base de middlewares de django
from django.utils.deprecation import MiddlewareMixin
# aqui importo las utilidades de tiempo para comparar instantes y sumar minutos
from django.utils import timezone
# aqui importo el sistema de autenticacion para cerrar la sesion del usuario
from django.contrib import auth
# aqui importo los mensajes para avisar que la sesion se cerro por inactividad
from django.contrib import messages
# aqui importo la configuracion del proyecto para leer el limite de inactividad
from django.conf import settings
# aqui importo el acceso mixto para poder redirigir al usuario al login
from django.shortcuts import redirect
# aqui importo el lector de fechas iso para reconstruir el instante guardado en la sesion
from django.utils.dateparse import parse_datetime
# aqui importo la clase datetime para distinguir el texto guardado de un instante real
from datetime import datetime, timedelta

# aqui defino la clave donde guardo en la sesion la ultima vez que el usuario hizo algo
CLAVE_ULTIMA_ACTIVIDAD = 'ultima_actividad'


# aqui defino el helper que transforma la marca de actividad en algo serializable por json
def leer_marca_actividad(sesion):
    # aqui rescato el valor crudo guardado bajo la clave de la marca de actividad
    crudo = sesion.get(CLAVE_ULTIMA_ACTIVIDAD)
    # aqui si no existe todavia la marca devuelvo nada para que el flujo siga su curso
    if crudo is None:
        return None
    # aqui si el valor ya es un datetime lo entrego directo sin volver a convertirlo
    if isinstance(crudo, datetime):
        return crudo
    # aqui si el valor es texto lo convierto de vuelta a un instante con zona horaria
    return parse_datetime(crudo)


class SesionInactivaMiddleware(MiddlewareMixin):
    # aqui defino la politica de expiracion: la sesion se cierra si el usuario no hace nada
    def process_request(self, request):
        # aqui solo me intereso por peticiones de usuarios que ya iniciaron sesion
        if not request.user.is_authenticated:
            return None
        # aqui obtengo la marca de tiempo de la ultima actividad guardada en la sesion
        ultima = leer_marca_actividad(request.session)
        # aqui obtengo el momento actual con zona horaria para poder comparar
        ahora = timezone.now()
        # aqui calculo cuantos minutos lleva el usuario sin realizar ninguna accion
        limite = timedelta(
            minutes=getattr(settings, 'DJANGO_SESSION_INACTIVIDAD_MINUTOS', 30)
        )
        # aqui reviso si existe una marca previa antes de aplicar el corte por inactividad
        if ultima is not None:
            # aqui calculo cuanto tiempo paso desde la ultima accion registrada
            inactivo = ahora - ultima
            # aqui si el tiempo supera el limite cierro la sesion por seguridad
            if inactivo > limite:
                # aqui obtengo el nombre del usuario antes de cerrar la sesion
                nombre = request.user.get_username()
                # aqui elimino la sesion por completo del servidor
                auth.logout(request)
                # aqui aviso al usuario que su sesion se cerro por inactividad
                messages.warning(
                    request,
                    f'Hola {nombre}, tu sesión se cerró por inactividad. Vuelve a iniciar sesión.',
                )
                # aqui redirijo al formulario de acceso para que pueda entrar de nuevo
                return redirect(settings.LOGIN_URL)
        # aqui registro la actividad actual para reiniciar el contador de inactividad
        # la sesion se firma con json por eso guardo el instante como texto iso 8601
        request.session[CLAVE_ULTIMA_ACTIVIDAD] = ahora.isoformat()
        # aqui devuelvo nada para que la peticion continue su recorrido normal
        return None
