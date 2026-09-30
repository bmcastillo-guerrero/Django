# aqui importo el modulo de administracion de django
from django.contrib import admin
# aqui importo el agregador para mostrar un total de stock al pie de la tabla del panel
from django.contrib.admin import SimpleListFilter
# aqui importo los mensajes del panel para informar el resultado de las acciones masivas
from django.contrib import messages
# aqui importo la traduccion de django para los titulos del panel en español
from django.utils.translation import gettext_lazy as _
# aqui importo la utilidad que escapa html para construir enlaces seguros en el panel
from django.utils.html import format_html
# aqui importo la expresion F del orm para comparar dos campos en un mismo filtro
from django.db.models import F
# aqui importo el logger del proyecto para auditar las acciones del administrador
import logging

# aqui importo los modelos del inventario para registrarlos
from .models import Categoria, MovimientoStock, Producto
# aqui importo el perfil de usuario para leer los nombres legibles de cada rol
from cuentas.models import PerfilUsuario
# aqui importo mis servicios transaccionales para reutilizar la logica de negocio en el panel
from .servicios import activar_productos, desactivar_productos, registrar_movimiento
# aqui importo el error de negocio base para capturar los rechazos de las acciones masivas
from .excepciones import ErrorNegocio

# aqui creo el logger propio de la configuracion del panel
logger = logging.getLogger('stockflow.admin')


# aqui defino un filtro lateral que separa los productos que ya necesitan reposicion
class StockBajoFilter(SimpleListFilter):
    # aqui escribo el titulo legible que aparecera sobre el filtro en el panel
    title = _('estado del stock')
    # aqui defino el nombre de la clave que se usa en la url del administrador
    parameter_name = 'stock_bajo'

    # aqui defino las opciones del filtro que el usuario puede seleccionar
    def lookups(self, request, model_admin):
        # aqui devuelvo la tupla con las opciones visibles del filtro lateral
        return (
            ('por_reponer', _('Necesitan reposición')),
            ('con_exceso', _('Con exceso')),
        )

    # aqui filtro la coleccion de productos segun la opcion que eligio el usuario
    def queryset(self, request, queryset):
        # aqui si eligio la opcion de productos que necesitan reposicion
        if self.value() == 'por_reponer':
            return queryset.filter(stock__lte=F('stock_minimo'))
        # aqui si eligio la opcion de productos con exceso de unidades
        if self.value() == 'con_exceso':
            return queryset.filter(stock__gt=F('stock_minimo'))
        # aqui si no eligio ninguna opcion devuelvo la coleccion completa
        return queryset


# aqui defino un filtro lateral que agrupa los productos segun el rol que los creo
class RolCreadoFilter(SimpleListFilter):
    # aqui escribo el titulo visible del filtro en el panel de administracion
    title = _('creado por rol')
    # aqui defino el nombre del parametro que viaja en la url del panel
    parameter_name = 'rol_creador'

    # aqui construyo las opciones del filtro usando los roles declarados en el perfil
    def lookups(self, request, model_admin):
        # aqui traduzco cada rol interno a su etiqueta legible como django choice field
        return [(clave, etiqueta) for clave, etiqueta in PerfilUsuario.ROLES]

    # aqui filtro la coleccion comparando el rol del usuario que creo cada producto
    def queryset(self, request, queryset):
        # aqui si el usuario no eligio opcion devuelvo la coleccion completa
        if not self.value():
            return queryset
        # aqui filtro por el rol exacto seleccionado en el filtro lateral
        return queryset.filter(creado_por__perfil__rol=self.value())


# aqui defino la accion masiva que desactiva los productos seleccionados en el panel
@admin.action(description=_('Marcar seleccionados como descontinuados'))
def accion_desactivar(modeladmin, request, queryset):
    # aqui delego la operacion al servicio transaccional del inventario
    total = desactivar_productos(queryset, usuario=request.user)
    # aqui informo al administrador quantos productos quedaron desactivados
    modeladmin.message_user(request, f'{total} producto(s) descontinuado(s).', messages.SUCCESS)


# aqui defino la accion masiva que reactiva los productos seleccionados en el panel
@admin.action(description=_('Reactivar seleccionados en el catálogo'))
def accion_activar(modeladmin, request, queryset):
    # aqui delego la operacion al servicio transaccional del inventario
    total = activar_productos(queryset, usuario=request.user)
    # aqui informo al administrador quantos productos volvieron al catalogo
    modeladmin.message_user(request, f'{total} producto(s) reactivado(s).', messages.SUCCESS)


# aqui defino la accion masiva que genera una entrada de inventario por producto elegido
@admin.action(description=_('Generar entrada de reposición por cada seleccionado'))
def accion_entrada_stock(modeladmin, request, queryset):
    # aqui inicializo un contador para informar cuantos productos aceptaron la entrada
    procesados = 0
    # aqui inicializo una lista para juntar los fallos sin interrumpir toda la accion
    fallidos = []
    # aqui recorro cada producto seleccionado en el panel
    for producto in queryset:
        # aqui intento registrar una entrada automatica de reposicion
        try:
            # aqui llamo al servicio con una cantidad igual al doble del stock minimo
            registrar_movimiento(
                producto=producto,
                tipo='ENTRADA',
                cantidad=max(producto.stock_minimo * 2, 1),
                observacion='Reposición automática desde el panel de administración',
                usuario=request.user,
            )
            # aqui sumo el producto a la lista de procesados con exito
            procesados += 1
        except ErrorNegocio as error:
            # aqui registro el fallo en el log para poder revisarlo despues
            logger.warning('No se pudo reponer %s: %s', producto.sku, error)
            # aqui guardo el sku del producto fallido para avisar al administrador
            fallidos.append(producto.sku)
    # aqui informo al administrador el resultado de la accion masiva
    modeladmin.message_user(
        request,
        f'{procesados} producto(s) repuesto(s). Fallaron: {", ".join(fallidos) or "ninguno"}.',
        messages.SUCCESS if not fallidos else messages.WARNING,
    )


# aqui personalizo los titulos del panel de control para que muestren la marca stockflow
admin.site.site_header = 'StockFlow — Panel de Inventario'
admin.site.site_title = 'StockFlow'
admin.site.index_title = 'Gestión de Bodega, Productos y Usuarios'


# aqui defino la clase para incrustar el historial de movimientos dentro de cada producto
class MovimientoStockInline(admin.TabularInline):
    # aqui indico que el inline se construye sobre el modelo de movimientos
    model = MovimientoStock
    # aqui no muestro formularios vacios porque los movimientos se registran desde la web
    extra = 0
    # aqui defino los campos que el administrador no puede editar a mano
    readonly_fields = ('fecha', 'registrado_por')
    # aqui permito ordenar el historial dentro de la ficha del producto
    ordering = ('-fecha',)
    # aqui defino el titulo del bloque de movimientos dentro del producto
    verbose_name = 'Movimiento de stock'
    # aqui defino el titulo en plural del bloque de movimientos
    verbose_name_plural = 'Historial de movimientos de este producto'
    # aqui limito cuantos movimientos se muestran en linea para no saturar la pagina
    def get_max_num(self, request, obj=None):
        return 10


# aqui registro y personalizo el modelo Categoria en el panel de administracion
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    # aqui defino las columnas visibles en la tabla del panel
    list_display = ('nombre', 'total_productos', 'descripcion', 'creado_por', 'boton_editar')
    # aqui agrego un buscador por el nombre de la categoria
    search_fields = ('nombre', 'descripcion')
    # aqui defino el orden alfabetico de las categorias
    ordering = ('nombre',)
    # aqui limito la cantidad de elementos por pagina
    list_per_page = 15
    # aqui defino que campos pueden editarse en el formulario del panel
    fields = ('nombre', 'descripcion', 'creado_por')
    # aqui defino las columnas editables directamente sobre la tabla del listado
    list_editable = ('descripcion',)
    # aqui defino el valor que se muestra cuando un campo opcional esta vacio
    empty_value_display = '—'

    # aqui defino una columna que muestra un enlace directo a la edicion de la categoria
    @admin.display(description='editar', ordering='nombre')
    def boton_editar(self, obj):
        # aqui importo el sistema de urls para construir el enlace al formulario
        from django.urls import reverse
        # aqui armo la url de edicion usando la clave primaria del objeto
        url_edicion = reverse('admin:inventario_categoria_change', args=[obj.pk])
        # aqui devuelvo un enlace seguro con html escapado por django
        return format_html('<a href="{}">Editar</a>', url_edicion)

    # aqui defino la accion masiva que elimina todas las categorias marcadas
    @admin.action(description=_('Eliminar categorías seleccionadas'))
    def accion_borrar_categorias(self, request, queryset):
        # aqui recorro cada categoria marcada para avisar si esta protegida
        protegidas = [cat.nombre for cat in queryset if cat.productos.exists()]
        # aqui filtro las categorias que si se pueden eliminar porque estan vacias
        eliminables = [cat for cat in queryset if not cat.productos.exists()]
        # aqui borro en una sola transaccion todas las categorias sin productos
        borrados, _ = Categoria.objects.filter(
            pk__in=[cat.pk for cat in eliminables]
        ).delete()
        # aqui informo al administrador cuantas categorias se eliminaron
        self.message_user(request, f'{borrados} categoría(s) eliminada(s).', messages.SUCCESS)
        # aqui si hubo categorias protegidas lo advierto para que limpie los productos
        if protegidas:
            self.message_user(
                request,
                f'No se pudieron eliminar (tienen productos): {", ".join(protegidas)}.',
                messages.WARNING,
            )


# aqui registro y personalizo el modelo Producto en el panel de administracion
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # aqui defino las columnas que se muestran en el listado de productos
    list_display = (
        'sku',
        'nombre',
        'categoria',
        'precio',
        'stock',
        'stock_minimo',
        'estado_stock',
        'activo',
        'actualizado_en',
    )
    # aqui agrego filtros laterales por categoria unidad estado activo y stock
    list_filter = ('categoria', 'unidad_medida', 'activo', StockBajoFilter, RolCreadoFilter)
    # aqui habilito la barra de busqueda por nombre o sku
    search_fields = ('nombre', 'sku')
    # aqui incrusto los movimientos de stock en la misma pantalla del producto
    inlines = [MovimientoStockInline]
    # aqui ordeno para que los productos mas nuevos salgan primero
    ordering = ('-fecha_registro',)
    # aqui configuro la paginacion profesional en el panel
    list_per_page = 25
    # aqui defino el filtro de ordenamiento rapido en la cabecera de la tabla
    list_select_related = ('categoria',)
    # aqui defino las acciones masivas disponibles en el panel
    actions = [accion_desactivar, accion_activar, accion_entrada_stock]
    # aqui defino que el filtro de categoria use el buscador dinamico de django
    autocomplete_fields = ('categoria',)
    # aqui defino el valor mostrado cuando un campo opcional esta vacio
    empty_value_display = '—'
    # aqui defino los grupos de campos del formulario de edicion
    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'sku', 'categoria', 'unidad_medida'),
        }),
        ('Inventario y precios', {
            'fields': ('precio', 'stock', 'stock_minimo', 'activo'),
        }),
        ('Auditoría', {
            'classes': ('collapse',),
            'fields': ('fecha_registro', 'actualizado_en', 'creado_por'),
        }),
    )
    # aqui defino los campos que solo se leen porque los calcula el sistema o el panel
    # las fechas usan auto_now_add y auto_now por eso django las marca como no editables
    readonly_fields = ('fecha_registro', 'actualizado_en')
    # aqui defino las columnas que se pueden modificar directo sobre la tabla
    list_editable = ('stock_minimo',)
    # aqui guardo el cambio en la parte superior e inferior del formulario largo
    save_on_top = True

    # aqui defino un metodo personalizado para mostrar visualmente el estado del stock
    @admin.display(description='Estado de stock', ordering='stock')
    def estado_stock(self, obj):
        # aqui devuelvo si requiere reponer segun la propiedad calculada
        return 'Reponer' if obj.necesita_reposicion else 'OK'

    # aqui defino el metodo que guarda el producto anotando la cuenta que lo creo
    def save_model(self, request, obj, form, change):
        # aqui si el producto es nuevo y no tiene autor se le asigna el usuario del panel
        if obj.pk is None and obj.creado_por_id is None:
            obj.creado_por = request.user
        # aqui delego el guardado al comportamiento estandar de django
        super().save_model(request, obj, form, change)


# aqui registro y personalizo el modelo de movimientos como coleccion independiente
@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    # aqui defino las columnas visibles del historial en el panel
    list_display = ('fecha', 'producto', 'tipo', 'cantidad', 'valor_movimiento', 'registrado_por')
    # aqui filtro por tipo de movimiento y por fecha de registro
    list_filter = ('tipo', 'fecha', 'producto__categoria')
    # aqui habilito la busqueda por sku nombre del producto y observacion
    search_fields = ('producto__sku', 'producto__nombre', 'observacion')
    # aqui cargo el producto de antemano para no hacer una consulta por cada fila
    list_select_related = ('producto', 'registrado_por')
    # aqui defino el filtro de ordenamiento por fecha en la cabecera
    date_hierarchy = 'fecha'
    # aqui limito la cantidad de movimientos por pagina
    list_per_page = 30
    # aqui defino el valor mostrado cuando un campo opcional esta vacio
    empty_value_display = '—'
    # aqui defino los campos que el administrador puede ver y editar en el panel
    fields = ('producto', 'tipo', 'cantidad', 'observacion', 'registrado_por', 'fecha')
    # aqui defino los campos que solo se pueden leer porque los calcula el sistema
    readonly_fields = ('fecha', 'valor_movimiento')
    # aqui defino el buscador dinamico para el campo producto
    autocomplete_fields = ('producto',)
    # aqui defino la columna que muestra el valor monetario de cada movimiento
    @admin.display(description='Valor del movimiento')
    def valor_movimiento(self, obj):
        # aqui uso la propiedad calculada del modelo para multiplicar precio por cantidad
        return f'${obj.valor_movimiento:,.0f}'

    # aqui defino el permiso por defecto que se concede al crear movimientos desde el panel
    def get_readonly_fields(self, request, obj=None):
        # aqui si el movimiento ya existe protejo el producto para no alterar el historial
        if obj is not None:
            # aqui devuelvo el producto como solo lectura junto a los campos ya protegidos
            return ('fecha', 'valor_movimiento', 'producto')
        # aqui para movimientos nuevos mantengo solo la fecha y el valor calculado
        return ('fecha', 'valor_movimiento')
