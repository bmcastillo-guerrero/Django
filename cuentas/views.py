# aqui importo las vistas genericas basadas en clases que usa django para el patron mvt
from django.contrib.auth import login
# aqui importo las vistas de autenticacion nativas que ya resuelven el inicio y cierre de sesion
from django.contrib.auth.views import LoginView, LogoutView
# aqui importo los mixins de acceso para exigir inicio de sesion en las rutas privadas
from django.contrib.auth.mixins import LoginRequiredMixin
# aqui importo las vistas genericas de listado y edicion de objetos
from django.views.generic import CreateView, ListView, UpdateView
# aqui importo las utilidades de render para las páginas simples de la aplicación
from django.shortcuts import render
# aqui importo el resolvedor de nombres de url para no dejar rutas relativas sueltas
from django.urls import reverse_lazy
# aqui importo los mensajes para avisar al usuario el resultado de cada operación
from django.contrib import messages
# aqui importo el modelo de usuario nativo de django para el listado de cuentas
from django.contrib.auth.models import User
# aqui importo el logger del proyecto para auditar los accesos al sistema
import logging

from .forms import FormularioIniciarSesion, FormularioPerfil, FormularioRegistro
from .models import PerfilUsuario
from .permisos import RolRequeridoMixin, es_administrador, etiqueta_rol

# aqui creo el logger propio para dejar rastro de cada inicio y cierre de sesión
logger = logging.getLogger('stockflow.cuentas')


class VistaIniciarSesion(LoginView):
    # aqui uso mi formulario estilizado en vez del formulario por defecto de django
    form_class = FormularioIniciarSesion
    # aqui indico la plantilla propia que se dibuja al pedir las credenciales
    template_name = 'cuentas/iniciar_sesion.html'
    # aqui defino la pagina extra que se mostrara a la izquierda del formulario
    extra_context = {'titulo': 'Iniciar sesión'}
    # aqui desactivo el redireccionamiento automatico para poder auditar y avisar
    redirect_authenticated_user = False

    # aqui personalizo el mensaje que se muestra cuando la sesion se inicia correctamente
    def form_valid(self, form):
        # aqui ejecuto el inicio de sesion nativo de django que crea la cookie firmada
        respuesta = super().form_valid(form)
        # aqui registro en el archivo de logs que usuario ingreso al sistema
        logger.info('Inicio de sesión: %s', self.request.user.get_username())
        # aqui aviso al usuario con un mensaje verde de acceso concedido
        messages.success(self.request, f'¡Bienvenido, {self.request.user.get_username()}!')
        # aqui devuelvo la redireccion hacia el panel principal
        return respuesta


class VistaCerrarSesion(LogoutView):
    # aqui solo permito el metodo post porque un enlace get permitiria cerrar la sesion ajena
    http_method_names = ['post', 'options']
    # aqui defino a donde vuelve el usuario despues de cerrar la sesion
    next_page = reverse_lazy('login')

    # aqui registro en el archivo de logs la salida del sistema antes de cerrar la sesion
    def post(self, request, *args, **kwargs):
        # aqui guardo el nombre del usuario antes de que django destruya la sesion
        nombre = request.user.get_username() if request.user.is_authenticated else 'anonimo'
        # aqui dejo la traza de seguridad en el archivo de registros
        logger.info('Cierre de sesión: %s', nombre)
        # aqui aviso al usuario que salio del sistema
        messages.info(request, 'Sesión cerrada correctamente.')
        # aqui delego el comportamiento nativo de cierre de sesion de django
        return super().post(request, *args, **kwargs)


class VistaRegistro(CreateView):
    # aqui vinculo el modelo que se creara con este formulario de alta
    model = User
    # aqui uso mi formulario de registro con validacion de contrasenas
    form_class = FormularioRegistro
    # aqui indico la plantilla que dibuja el formulario de alta de cuenta
    template_name = 'cuentas/registro.html'
    # aqui defino la pagina a la que se va despues de crear la cuenta
    # uso reverse_lazy porque un nombre de ruta suelto se resolveria contra la url actual
    success_url = reverse_lazy('perfil')

    # aqui ajusto el contexto para mostrar los roles disponibles en la pantalla de alta
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto estandar del formulario
        contexto = super().get_context_data(**kwargs)
        # aqui agrego el titulo de la pagina
        contexto['titulo'] = 'Crear cuenta'
        # aqui devuelvo el contexto completo a la plantilla
        return contexto

    # aqui guardo la cuenta y ademas inicio la sesion del nuevo usuario automaticamente
    def form_valid(self, form):
        # aqui obtengo la cuenta recien creada con todos sus datos validados
        respuesta = super().form_valid(form)
        # aqui inicio la sesion del usuario recien registrado para que entre directo
        login(self.request, self.object)
        # aqui aviso que la cuenta fue creada y que parte como vendedor
        messages.success(
            self.request,
            'Cuenta creada. Tu perfil nació como Vendedor por seguridad; '
            'un administrador puede elevar tu rol.',
        )
        # aqui devuelvo la redireccion configurada en success_url
        return respuesta


class VistaPerfil(LoginRequiredMixin, UpdateView):
    # aqui defino que siempre se editara el perfil del usuario que esta conectado
    model = PerfilUsuario
    # aqui uso el formulario que edita a la vez la cuenta y el perfil
    form_class = FormularioPerfil
    # aqui indico la plantilla que dibuja la ficha del usuario
    template_name = 'cuentas/perfil.html'
    # aqui defino la pagina de destino despues de guardar los cambios
    success_url = reverse_lazy('perfil')

    # aqui defino que objeto se va a editar tomando siempre el perfil del usuario conectado
    def get_object(self, queryset=None):
        # aqui busco el perfil asociado al usuario que inicio sesion
        return PerfilUsuario.objects.select_related('usuario').get(usuario=self.request.user)

    # aqui armo el contexto de la pagina con los grupos y permisos heredados de django
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para traer el formulario ya construido
        contexto = super().get_context_data(**kwargs)
        # aqui agrego el titulo de la ficha personal
        contexto['titulo'] = 'Mi perfil'
        # aqui entrego los grupos de django a los que pertenece el usuario
        contexto['grupos'] = self.request.user.groups.all()
        # aqui entrego una etiqueta legible del rol actual
        contexto['rol_actual'] = etiqueta_rol(self.request.user)
        # aqui entrego los permisos efectivos de la cuenta
        contexto['permisos'] = sorted(self.request.user.get_all_permissions())
        # aqui devuelvo el contexto a la plantilla
        return contexto

    # aqui aviso al usuario que su informacion quedo actualizada
    def form_valid(self, form):
        # aqui ejecuto el guardado normal del formulario y su redireccion
        respuesta = super().form_valid(form)
        # aqui confirmo el cambio con un mensaje verde
        messages.success(self.request, 'Tus datos de perfil fueron actualizados.')
        # aqui devuelvo la respuesta con la redireccion
        return respuesta


class VistaListaUsuarios(RolRequeridoMixin, LoginRequiredMixin, ListView):
    # aqui defino el modelo de la coleccion de cuentas que se listara
    model = User
    # aqui indico la plantilla que dibuja la tabla de cuentas
    template_name = 'cuentas/lista_usuarios.html'
    # aqui defino cuantos registros se muestran por pagina
    paginate_by = 15
    # aqui el contexto que se envia a la plantilla
    context_object_name = 'usuarios'

    # aqui solo los administradores pueden ver esta coleccion de cuentas
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR]

    # aqui consulto la coleccion Trazando la relacion con el perfil y los grupos
    def get_queryset(self):
        # aqui base vacia con el perfil y los grupos ya cargados para evitar consultas repetidas
        return User.objects.select_related('perfil').prefetch_related('groups').order_by('username')

    # aqui agrego al contexto el titulo y la cantidad total de cuentas registradas
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto estandar de la lista
        contexto = super().get_context_data(**kwargs)
        # aqui agrego el titulo de la pagina de gestion de cuentas
        contexto['titulo'] = 'Cuentas del sistema'
        # aqui agrego el total de cuentas para mostrarlo como metrica
        contexto['total_cuentas'] = self.get_queryset().count()
        # aqui devuelvo el contexto completo a la plantilla
        return contexto
