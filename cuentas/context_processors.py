# aqui importo la funcion que arma el contexto que veran todas las plantillas
from django.utils import timezone

# aqui importo el helper del middleware que reconstruye la marca de actividad
from cuentas.middleware import leer_marca_actividad
# aqui importo la configuracion del proyecto para conocer el limite de inactividad
from django.conf import settings
# aqui importo el helper que traduce el rol del usuario a una etiqueta legible
from cuentas.permisos import etiqueta_rol


# aqui defino el context processor que agrega los datos de sesion a todas las plantillas
def sesion(request):
    # aqui parto de un contexto vacio para las visitas anonimas
    contexto = {'minutos_sesion_restantes': None, 'rol_actual': None}
    # aqui solo calculo los datos de sesion si el usuario ya inicio sesion
    if not request.user.is_authenticated:
        return contexto
    # aqui obtengo la marca de la ultima actividad registrada por el middleware
    ultima = leer_marca_actividad(request.session)
    # aqui si no existe la marca todavia no puedo calcular el tiempo restante
    if ultima is None:
        return contexto
    # aqui calculo cuantos minutos lleva el usuario sin hacer nada
    limite = getattr(settings, 'DJANGO_SESSION_INACTIVIDAD_MINUTOS', 30)
    # aqui calculo los minutos transcurridos desde la ultima actividad
    inactivos = (timezone.now() - ultima).total_seconds() / 60
    # aqui calculo los minutos que le quedan antes de que se cierre la sesion
    restantes = int(limite - inactivos)
    # aqui entrego el valor maximo con cero para que la barra no se vea negativa
    contexto['minutos_sesion_restantes'] = max(restantes, 0)
    # aqui entrego tambien el nombre del rol para mostrarlo en la barra de navegacion
    contexto['rol_actual'] = etiqueta_rol(request.user)
    # aqui devuelvo el contexto con los datos de sesion listos para las plantillas
    return contexto
