# aqui importo el modelo de usuario nativo de django que sera la base de mis cuentas
from django.contrib.auth.models import User
# aqui importo las herramientas de modelos para declarar campos y relaciones
from django.db import models


class PerfilUsuario(models.Model):
    # aqui defino las opciones de rol que tendrá cada usuario dentro de la aplicación
    ADMINISTRADOR = 'ADMINISTRADOR'
    BODEGUERO = 'BODEGUERO'
    VENDEDOR = 'VENDEDOR'

    ROLES = [
        (ADMINISTRADOR, 'Administrador'),
        (BODEGUERO, 'Bodeguero'),
        (VENDEDOR, 'Vendedor'),
    ]

    # aqui vinculo el perfil con una cuenta de django usando una relacion uno a uno
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='usuario',
    )
    # aqui guardo el rol asignado que controla que puede hacer la persona dentro del sistema
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default=VENDEDOR,
        verbose_name='rol',
    )
    # aqui guardo un contacto opcional para avisar de faltantes de stock
    telefono = models.CharField(max_length=20, blank=True, verbose_name='teléfono')
    # aqui registro cuando se creo el perfil para auditar el alta de cuentas
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='creado en')

    class Meta:
        # aqui escribo el nombre legible del modelo en singular y plural
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'
        # aqui ordeno el listado por rol para que sea mas facil de revisar en el administrador
        ordering = ['rol', 'usuario__username']
        # aqui creo permisos finos que luego asigno a los grupos segun el rol
        permissions = [
            ('puede_asignar_roles', 'Puede asignar y cambiar roles de los usuarios'),
            ('puede_ver_cuentas', 'Puede ver el listado de cuentas del sistema'),
        ]

    # aqui defino la representacion en texto para mostrar el nombre de la cuenta
    def __str__(self):
        return f'{self.usuario.username} · {self.get_rol_display()}'

    # aqui entrego el nombre real del usuario usando el campo first_name
    @property
    def nombre_completo(self):
        # aqui armo el nombre juntando nombre y apellido de la cuenta
        completo = self.usuario.get_full_name().strip()
        # aqui devuelvo el nombre completo o el usuario si la persona no registro nombre
        return completo or self.usuario.username

    # aqui entrego las iniciales para mostrar un avatar con letras en la interfaz
    @property
    def iniciales(self):
        # aqui parto de las iniciales del nombre completo en mayusculas
        partes = self.nombre_completo.split()
        # aqui si la persona no registro nombre real uso las dos primeras letras del usuario
        if len(partes) < 2:
            return partes[0][:2].upper() if partes else 'SF'
        # aqui tomo la primera letra de cada parte y las uno en un solo texto
        return ''.join(parte[0] for parte in partes[:2]).upper()

    # aqui indica si el usuario tiene el rol de administrador del sistema
    @property
    def es_administrador(self):
        return self.rol == self.ADMINISTRADOR

    # aqui indica si el usuario tiene el rol de bodeguero
    @property
    def es_bodeguero(self):
        return self.rol == self.BODEGUERO

    # aqui indica si el usuario tiene el rol de vendedor
    @property
    def es_vendedor(self):
        return self.rol == self.VENDEDOR
