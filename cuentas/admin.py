# aqui importo el modulo de administracion de django
from django.contrib import admin
# aqui importo el modelo de usuario nativo para poder extender su registro en el panel
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# aqui importo mi modelo de perfil para registrarlo en el panel
from .models import PerfilUsuario
# aqui importo el nombre de mis grupos para que el panel muestre el rol del usuario
from .roles import MAPA_ROL_GRUPO


# aqui creo un inline para que el perfil del usuario aparezca dentro de su ficha de usuario
class PerfilUsuarioInline(admin.StackedInline):
    # aqui indico que el perfil se administra dentro de la cuenta y no por separado
    model = PerfilUsuario
    # aqui no permito agregar perfiles adicionales desde la ficha del usuario
    can_delete = False
    # aqui defino los campos que solo se pueden leer porque los calcula el sistema
    readonly_fields = ('creado_en',)
    # aqui limito la cantidad de formularios vacios que se muestran
    extra = 0
    # aqui defino el titulo del bloque que aparece en la pagina del usuario
    verbose_name = 'Perfil de StockFlow'
    # aqui defino el titulo en plural del bloque del panel
    verbose_name_plural = verbose_name


# aqui desregistro el registro original de usuario para poder reemplazarlo por el meu
admin.site.unregister(User)


# aqui registro el modelo usuario con una version extendida que incluye el perfil y el rol
@admin.register(User)
class UsuarioAdmin(BaseUserAdmin):
    # aqui mantengo toda la configuracion original de django y agrego mis columnas
    list_display = (
        'username',
        'email',
        'nombre_completo',
        'rol_actual',
        'is_staff',
        'is_active',
    )
    # aqui agrego un buscador por nombre correo y nombre real del usuario
    search_fields = ('username', 'email', 'first_name', 'last_name')
    # aqui agrego filtros laterales por rol activo y permisos de staff
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    # aqui defino el titulo de la columna con el nombre real del usuario
    def nombre_completo(self, obj):
        # aqui devuelvo el nombre y apellido unidos o el usuario si no hay nombre
        return obj.get_full_name() or obj.username
    # aqui defino el encabezado de la columna del nombre completo
    nombre_completo.short_description = 'Nombre'
    # aqui defino la columna que muestra el rol asignado dentro del sistema
    def rol_actual(self, obj):
        # aqui busco el perfil del usuario con una sola consulta a la base
        perfil = getattr(obj, 'perfil', None)
        # aqui devuelvo el nombre del rol o un guion si la cuenta aun no tiene perfil
        return perfil.get_rol_display() if perfil else '—'
    # aqui defino el encabezado de la columna del rol
    rol_actual.short_description = 'Rol'
    # aqui coloco el perfil embebido dentro de la ficha del usuario para editarlo en el mismo lugar
    inlines = [PerfilUsuarioInline]
    # aqui defino los grupos de campos en el formulario de alta del panel
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Datos de contacto', {'fields': ('email', 'first_name', 'last_name')}),
    )


# aqui registro y personalizo el perfil para que los administradores asignen roles facilmente
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    # aqui defino las columnas visibles en el listado de perfiles
    list_display = ('usuario', 'nombre_completo', 'rol', 'grupo_asignado', 'creado_en')
    # aqui agrego un buscador por nombre de usuario y rol
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'rol')
    # aqui agrego un filtro lateral rapido por cada rol
    list_filter = ('rol',)
    # aqui defino los grupos de campos del formulario de edicion
    fieldsets = (
        ('Cuenta', {'fields': ('usuario',)}),
        ('Perfil y permisos', {'fields': ('rol', 'telefono')}),
        ('Auditoría', {'fields': ('creado_en',)}),
    )
    # aqui defino la columna que muestra a que grupo de django pertenece la cuenta
    def grupo_asignado(self, obj):
        # aqui traduzco el rol al nombre del grupo usando el mapa central de roles
        return MAPA_ROL_GRUPO.get(obj.rol, '—')
    # aqui defino el encabezado de la columna del grupo asignado
    grupo_asignado.short_description = 'Grupo Django'
    # aqui limito la cantidad de perfiles por pagina
    list_per_page = 20
