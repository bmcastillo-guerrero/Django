# aqui importo el mixin de control de acceso de django para reutilizar su logica de negacion
from django.contrib.auth.mixins import AccessMixin
# aqui importo el perfil para comparar contra los roles definidos
from .models import PerfilUsuario


# aqui defino una funcion segura que devuelve el perfil o un perfil vacio si no existe
def perfil_de(usuario):
    # aqui protejo contra usuarios anonimos que no tienen atributo perfil
    if not usuario or not usuario.is_authenticated:
        return None
    # aqui devuelvo el perfil asociado usando la relacion inversa de django
    return getattr(usuario, 'perfil', None)


# aqui indica si la cuenta actua como administrador del sistema
def es_administrador(usuario):
    # aqui los superusuarios de django siempre se consideran administradores
    if usuario and usuario.is_superuser:
        return True
    # aqui obtengo el perfil para revisar el rol asignado
    perfil = perfil_de(usuario)
    # aqui devuelvo True solo si el perfil existe y tiene el rol de administrador
    return bool(perfil and perfil.es_administrador)


# aqui indica si la cuenta actua como bodeguero
def es_bodeguero(usuario):
    # aqui obtengo el perfil para revisar el rol asignado
    perfil = perfil_de(usuario)
    # aqui devuelvo True solo si el perfil existe y tiene el rol de bodeguero
    return bool(perfil and perfil.es_bodeguero)


# aqui indica si la cuenta actua como vendedor
def es_vendedor(usuario):
    # aqui obtengo el perfil para revisar el rol asignado
    perfil = perfil_de(usuario)
    # aqui devuelvo True solo si el perfil existe y tiene el rol de vendedor
    return bool(perfil and perfil.es_vendedor)


# aqui indica si la cuenta puede crear y modificar el catalogo de productos
def puede_gestionar_catalogo(usuario):
    # aqui los administradores y bodegueros pueden gestionar el catalogo
    return es_administrador(usuario) or es_bodeguero(usuario)


# aqui indica si la cuenta puede registrar entradas y salidas de mercaderia
def puede_registrar_movimientos(usuario):
    # aqui los administradores y bodegueros pueden mover inventario
    return es_administrador(usuario) or es_bodeguero(usuario)


# aqui indica si la cuenta puede eliminar registros del catalogo
def puede_eliminar_productos(usuario):
    # aqui solo los administradores tienen el permiso de eliminar
    return es_administrador(usuario)


# aqui indica si la cuenta puede ver y administrar las cuentas de usuarios
def puede_gestionar_cuentas(usuario):
    # aqui solo los administradores acceden a la gestion de cuentas
    return es_administrador(usuario)


# aqui traduce un rol a una etiqueta corta para mostrar en la interfaz
def etiqueta_rol(usuario):
    # aqui obtengo el perfil de la cuenta
    perfil = perfil_de(usuario)
    # aqui devuelvo el nombre del rol o la palabra sin rol si no tiene perfil
    return perfil.get_rol_display() if perfil else 'Sin rol'


class RolRequeridoMixin(AccessMixin):
    # aqui declaro la lista de roles permitidos que cada vista sobreescribira
    roles_permitidos = []

    # aqui valido el rol del usuario antes de ejecutar la vista protegida
    def dispatch(self, request, *args, **kwargs):
        # aqui obtengo el perfil del usuario que intenta entrar
        perfil = perfil_de(request.user)
        # aqui defino el rol real del usuario o una cadena vacia si no tiene perfil
        rol_actual = perfil.rol if perfil else ''
        # aqui permito el paso a superusuarios de django porque son la raiz del sistema
        if not request.user.is_superuser and rol_actual not in self.roles_permitidos:
            # aqui niego el acceso usando la respuesta 403Forbidden
            return self.handle_no_permission()
        # aqui si el rol es correcto dejo continuar la peticion
        return super().dispatch(request, *args, **kwargs)
