# aqui importo la configuracion de django para registrar correctamente la aplicacion
from django.apps import AppConfig


class CuentasConfig(AppConfig):
    # aqui defino el nombre tecnico de la aplicacion de cuentas
    name = 'cuentas'
    # aqui defino el nombre visible que aparece en el panel de administracion
    verbose_name = 'Cuentas, sesiones y roles'
    # aqui le indico a django que use el archivo de configuracion de esta clase
    default_auto_field = 'django.db.models.BigAutoField'
    # aqui conecto las señales que crean el perfil y los permisos al iniciar la aplicacion
    def ready(self):
        # aqui importo el modulo de señales para que quede registrado en el proceso
        from . import signals  # noqa: F401
