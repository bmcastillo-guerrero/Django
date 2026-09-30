# aqui importo las vistas genéricas de django que implementan el patron mvt sobre clases
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
# aqui importo las utilidades de url para resolver rutas y redirecciones por nombre
from django.urls import reverse_lazy
# aqui importo el mixin de inicio de sesion para bloquear las rutas privadas a anonimos
from django.contrib.auth.mixins import LoginRequiredMixin
# aqui importo los mixins de mensajes para avisar el resultado de cada operacion
from django.contrib.messages.views import SuccessMessageMixin
# aqui importo las utilidades de redireccion y render
from django.shortcuts import redirect
# aqui importo el sistema de mensajes para avisar al usuario
from django.contrib import messages
# aqui importo el error de integridad referencial para controlar el borrado de categorias
from django.db.models import ProtectedError
# aqui importo el logger del proyecto para auditar las operaciones del catalogo
import logging

# aqui importo los formularios y modelos del inventario
from .forms import (
    AjusteStockForm,
    CategoriaForm,
    FiltroMovimientosForm,
    MovimientoForm,
    ProductoForm,
)
from .models import Categoria, MovimientoStock, Producto
from .selectores import (
    categorias_con_conteo,
    historial_movimientos,
    metricas_dashboard,
    productos_filtrados,
    productos_por_reponer,
)
from .servicios import (
    activar_productos,
    desactivar_productos,
    ajustar_stock,
    registrar_movimiento,
)

# aqui importo el mixin de rol y el perfil para restringir el acceso segun el perfil del usuario
from cuentas.models import PerfilUsuario
from cuentas.permisos import (
    RolRequeridoMixin,
    puede_eliminar_productos,
    puede_gestionar_catalogo,
    puede_registrar_movimientos,
)

# aqui creo el logger propio de la capa de vistas del inventario
logger = logging.getLogger('stockflow.inventario')


# aqui defino la clase base que agrupa los permisos y el contexto comun de todas las vistas
class BaseInventarioView(LoginRequiredMixin):
    # aqui defino los roles que pueden crear y modificar el catalogo de productos
    roles_catalogo = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui defino los roles que pueden registrar entradas y salidas de mercaderia
    roles_movimientos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui defino los roles que pueden eliminar registros del catalogo
    roles_borrado = [PerfilUsuario.ADMINISTRADOR]

    # aqui agrego al contexto los datos de sesion que la barra de navegacion necesita
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto estandar de la vista
        contexto = super().get_context_data(**kwargs)
        # aqui indico si la cuenta actual puede crear y editar productos
        contexto['puede_gestionar_catalogo'] = puede_gestionar_catalogo(self.request.user)
        # aqui indico si la cuenta actual puede registrar movimientos
        contexto['puede_registrar_movimientos'] = puede_registrar_movimientos(self.request.user)
        # aqui indico si la cuenta actual puede eliminar productos
        contexto['puede_eliminar_productos'] = puede_eliminar_productos(self.request.user)
        # aqui devuelvo el contexto con los permisos ya resueltos
        return contexto


# aqui defino la vista del panel principal con las metricas calculadas por el selector
class VistaDashboard(BaseInventarioView, TemplateView):
    # aqui indico la plantilla que dibuja el panel de control
    template_name = 'inventario/dashboard.html'

    # aqui armo el contexto del panel usando los selectores y no el orm en la vista
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original que agrega los permisos comunes
        contexto = super().get_context_data(**kwargs)
        # aqui pido al selector las metricas agregadas calculadas en la base de datos
        metricas = metricas_dashboard()
        # aqui copio cada metrica calculada al contexto de la plantilla
        contexto['total_productos'] = metricas['total_productos']
        contexto['total_unidades'] = metricas['total_unidades']
        contexto['valor_inventario'] = metricas['valor_inventario']
        contexto['total_movimientos'] = metricas['total_movimientos']
        # aqui agrego el titulo de la pagina del panel
        contexto['titulo'] = 'Panel de inventario'
        # aqui pido los productos que ya llegaron a su stock minimo
        contexto['por_reponer'] = productos_por_reponer(limite=8)
        # aqui cargo las categorias con su conteo de productos para los filtros rapidos
        contexto['categorias'] = categorias_con_conteo()
        # aqui cargo los ultimos movimientos para la tabla de actividad reciente
        contexto['ultimos_movimientos'] = historial_movimientos(limite=8)
        # aqui devuelvo el contexto completo al panel
        return contexto


# aqui defino la vista de la coleccion de productos con busqueda filtro orden y paginacion
class VistaListaProductos(BaseInventarioView, ListView):
    # aqui defino el modelo de la coleccion que se va a listar
    model = Producto
    # aqui indico la plantilla que dibuja la tabla de productos
    template_name = 'inventario/lista_productos.html'
    # aqui defino el nombre de la variable que recibe la coleccion en la plantilla
    context_object_name = 'productos'
    # aqui defino cuantos productos se muestran por pagina
    paginate_by = 12
    # aqui defino el titulo base de la pagina
    titulo_pagina = 'Productos'

    # aqui entrego la coleccion filtrada y ordenada usando la capa de selectores
    def get_queryset(self):
        # aqui leo el texto del buscador enviado por el usuario
        query = self.request.GET.get('q', '').strip()
        # aqui leo la categoria seleccionada en el filtro lateral
        categoria_id = self.request.GET.get('categoria', '').strip()
        # aqui leo el criterio de ordenamiento elegido por el usuario
        orden = self.request.GET.get('orden', 'recientes')
        # aqui entrego al selector la coleccion ya filtrada con esos tres parametros
        return productos_filtrados(query, categoria_id, orden)

    # aqui agrego al contexto los filtros activos y las categorias disponibles
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto de la lista paginada
        contexto = super().get_context_data(**kwargs)
        # aqui agrego el titulo de la pagina de catalogo
        contexto['titulo'] = 'Catálogo de productos'
        # aqui devuelvo al formulario los filtros enviados para no perderlos al escribir
        contexto['query'] = self.request.GET.get('q', '').strip()
        # aqui mantengo activa la categoria seleccionada en la interfaz
        contexto['categoria_id'] = self.request.GET.get('categoria', '').strip()
        # aqui mantengo activo el criterio de ordenamiento en la interfaz
        contexto['orden'] = self.request.GET.get('orden', 'recientes')
        # aqui cargo las categorias con conteo para pintar los botones de filtro rapido
        contexto['categorias'] = categorias_con_conteo()
        # aqui entrego el total de la coleccion antes de paginar para mostrarlo como metrica
        contexto['total_resultados'] = self.get_queryset().count()
        # aqui devuelvo el contexto completo a la plantilla
        return contexto


# aqui defino la vista de detalle que muestra la ficha y el historial del producto
class VistaDetalleProducto(BaseInventarioView, DetailView):
    # aqui defino el modelo de la ficha que se muestra
    model = Producto
    # aqui indico la plantilla de la ficha completa del producto
    template_name = 'inventario/detalle_producto.html'
    # aqui defino el titulo base de la pagina
    titulo_pagina = 'Detalle del producto'

    # aqui cargo el producto con su categoria y su creador ya relacionados
    def get_queryset(self):
        return Producto.objects.select_related('categoria', 'creado_por')

    # aqui agrego el historial, los formularios y los permisos al contexto de la ficha
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto estandar del detalle
        contexto = super().get_context_data(**kwargs)
        # aqui cargo los ultimos movimientos del producto con su usuario responsable
        contexto['movimientos'] = self.object.movimientos.select_related('registrado_por')[:25]
        # aqui entrego el formulario de movimiento listo para pintar en la pantalla
        contexto['form_movimiento'] = MovimientoForm(initial={'tipo': 'ENTRADA'})
        # aqui entrego el formulario de ajuste manual de stock
        contexto['form_ajuste'] = AjusteStockForm()
        # aqui indico si la cuenta puede registrar movimientos sobre este producto
        contexto['puede_registrar_movimientos'] = puede_registrar_movimientos(self.request.user)
        # aqui indico si la cuenta puede hacer ajustes directos de stock
        contexto['puede_ajustar_stock'] = self.request.user.has_perm(
            'inventario.puede_ajustar_stock'
        )
        # aqui devuelvo el contexto completo a la plantilla
        return contexto


# aqui defino la vista que procesa el registro de entradas y salidas de mercaderia
class VistaRegistrarMovimiento(RolRequeridoMixin, LoginRequiredMixin, CreateView):
    # aqui defino el modelo que se creara al registrar el movimiento
    model = MovimientoStock
    # aqui uso el formulario de movimiento con validacion contra el stock real
    form_class = MovimientoForm
    # aqui indico la plantilla de confirmacion usada cuando el formulario no es valido
    template_name = 'inventario/detalle_producto.html'
    # aqui limito el acceso solo a administradores y bodegueros
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]

    # aqui defino el producto sobre el que se va a registrar el movimiento
    def obtener_producto(self):
        # aqui busco el producto por su clave primaria en la url
        return Producto.objects.select_related('categoria').get(pk=self.kwargs['pk'])

    # aqui entrego al formulario el producto para que pueda validar el stock disponible
    def get_form_kwargs(self):
        # aqui parto de los argumentos que arma el constructor del formulario
        argumentos = super().get_form_kwargs()
        # aqui agrego el producto como atributo extra del formulario
        argumentos['producto'] = self.obtener_producto()
        # aqui devuelvo los argumentos completos al constructor
        return argumentos

    # aqui intercepto el envio valido para usar el servicio transaccional de inventario
    def form_valid(self, form):
        # aqui obtengo el producto destino del movimiento
        producto = self.obtener_producto()
        # aqui llamo al servicio que aplica la regla de negocio dentro de una transaccion
        registrar_movimiento(
            producto=producto,
            tipo=form.cleaned_data['tipo'],
            cantidad=form.cleaned_data['cantidad'],
            observacion=form.cleaned_data.get('observacion', ''),
            usuario=self.request.user,
        )
        # aqui aviso al usuario que el movimiento quedo registrado
        messages.success(self.request, 'Movimiento registrado correctamente.')
        # aqui redirijo de vuelta a la ficha del producto
        return redirect('detalle_producto', pk=producto.pk)

    # aqui capturo los errores de negocio del servicio para mostrarlos sin traceback
    def form_invalid(self, form):
        # aqui vuelvo a la ficha del producto pasando el formulario con su error visible
        producto = self.obtener_producto()
        # aqui agrego un mensaje de error explicando que el movimiento fue rechazado
        messages.error(self.request, 'No se pudo registrar el movimiento.')
        # aqui redirijo a la ficha para que el usuario vea el detalle del error
        return redirect('detalle_producto', pk=producto.pk)

    # aqui defino a donde se reenvia al usuario cuando el formulario tiene errores
    def get_success_url(self):
        # aqui nunca se usa porque el guardado se hace en el servicio de inventario
        return reverse_lazy('detalle_producto', kwargs={'pk': self.kwargs['pk']})


# aqui defino la vista que permite el ajuste directo de stock para quien tenga el permiso
class VistaAjustarStock(RolRequeridoMixin, LoginRequiredMixin, FormView):
    # aqui uso el formulario de ajuste manual de stock
    form_class = AjusteStockForm
    # aqui limito el acceso a administradores y bodegueros
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui defino la pagina de destino cuando el formulario no es valido
    template_name = 'inventario/detalle_producto.html'
    # aqui defino el titulo base de la pagina
    titulo_pagina = 'Ajuste de stock'

    # aqui valido que la cuenta tenga el permiso fino de ajuste directo de stock
    def dispatch(self, request, *args, **kwargs):
        # aqui reviso el permiso antes de ejecutar cualquier logica de la vista
        if request.user.is_authenticated and not request.user.has_perm(
            'inventario.puede_ajustar_stock'
        ):
            # aqui niego el acceso mostrando la pagina de error 403
            messages.error(request, 'Tu rol no permite ajustar el stock directamente.')
            # aqui redirijo al panel para que el usuario no quede en una pagina vacia
            return redirect('dashboard')
        # aqui si tiene el permiso dejo continuar la peticion hacia el formulario
        return super().dispatch(request, *args, **kwargs)

    # aqui entrego al servicio el nuevo valor de stock solicitado por el usuario
    def form_valid(self, form):
        # aqui busco el producto que se quiere ajustar por su clave primaria
        producto = Producto.objects.get(pk=self.kwargs['pk'])
        # aqui llamo al servicio transaccional que escribe el nuevo stock
        ajustar_stock(
            producto=producto,
            nuevo_stock=form.cleaned_data['nuevo_stock'],
            usuario=self.request.user,
        )
        # aqui aviso al usuario que el ajuste quedo aplicado
        messages.success(self.request, f'Stock de {producto.nombre} ajustado.')
        # aqui redirijo a la ficha del producto para ver el resultado
        return redirect('detalle_producto', pk=producto.pk)


# aqui defino la vista de alta de productos en el catalogo
class VistaCrearProducto(RolRequeridoMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    # aqui defino el modelo que se creara con el formulario
    model = Producto
    # aqui uso el formulario de producto con validaciones rigurosas
    form_class = ProductoForm
    # aqui indico la plantilla que dibuja el formulario de alta
    template_name = 'inventario/form_producto.html'
    # aqui defino la pagina de destino despues de crear el producto
    success_url = reverse_lazy('lista_productos')
    # aqui limito el acceso a administradores y bodegueros
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui escribo el mensaje de exito que vera el usuario tras crear el registro
    success_message = 'Producto creado correctamente en el catálogo.'

    # aqui entrego el usuario actual al formulario para aplicar los permisos de campo
    def get_form_kwargs(self):
        # aqui parto de los argumentos que arma el constructor del formulario
        argumentos = super().get_form_kwargs()
        # aqui agrego el usuario conectado para que el formulario sepa que campos mostrar
        argumentos['usuario'] = self.request.user
        # aqui devuelvo los argumentos completos al constructor
        return argumentos

    # aqui completo los datos automaticos que el usuario no debe escribir a mano
    def form_valid(self, form):
        # aqui asigno al producto la cuenta que esta creando el registro
        form.instance.creado_por = self.request.user
        # aqui delego el guardado normal del formulario al comportamiento estandar
        return super().form_valid(form)

    # aqui agrego el titulo de la pagina segun se este creando o no un producto
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto del formulario
        contexto = super().get_context_data(**kwargs)
        # aqui indico el titulo visible en el encabezado de la pagina
        contexto['titulo'] = 'Nuevo producto'
        # aqui devuelvo el contexto a la plantilla
        return contexto


# aqui defino la vista de edicion de un producto existente
class VistaEditarProducto(RolRequeridoMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    # aqui defino el modelo que se va a modificar
    model = Producto
    # aqui uso el mismo formulario de alta pero apuntando a la instancia existente
    form_class = ProductoForm
    # aqui indico la plantilla compartida de alta y edicion
    template_name = 'inventario/form_producto.html'
    # aqui defino la pagina de destino despues de guardar los cambios
    success_url = reverse_lazy('lista_productos')
    # aqui limito el acceso a administradores y bodegueros
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui escribo el mensaje de exito que vera el usuario tras editar el registro
    success_message = 'Producto actualizado correctamente.'

    # aqui entrego el usuario actual al formulario para aplicar los permisos de campo
    def get_form_kwargs(self):
        # aqui parto de los argumentos que arma el constructor del formulario
        argumentos = super().get_form_kwargs()
        # aqui agrego el usuario conectado para que el formulario sepa que campos mostrar
        argumentos['usuario'] = self.request.user
        # aqui devuelvo los argumentos completos al constructor
        return argumentos

    # aqui agrego el titulo con el nombre del producto que se esta editando
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto del formulario
        contexto = super().get_context_data(**kwargs)
        # aqui armo un titulo descriptivo con el nombre del producto en edicion
        contexto['titulo'] = f'Editar: {self.object.nombre}'
        # aqui devuelvo el contexto a la plantilla
        return contexto


# aqui defino la vista de eliminacion de un producto con confirmacion previa
class VistaEliminarProducto(RolRequeridoMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    # aqui defino el modelo que se va a eliminar
    model = Producto
    # aqui indico la plantilla de confirmacion con advertencias
    template_name = 'inventario/eliminar_producto.html'
    # aqui defino la pagina de destino despues de eliminar el registro
    success_url = reverse_lazy('lista_productos')
    # aqui limito el borrado solo a administradores del sistema
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR]
    # aqui escribo el mensaje de exito que vera el usuario tras eliminar el registro
    success_message = 'Producto eliminado del catálogo.'

    # aqui registro en el log que registro se va a eliminar antes de hacerlo
    def form_valid(self, form):
        # aqui guardo el nombre del producto para dejarlo escrito en la bitacora
        nombre = self.object.nombre
        # aqui registro la accion del usuario en el archivo de logs
        logger.info(
            'Eliminación del producto %s por %s', nombre, self.request.user.get_username()
        )
        # aqui delego el borrado real al comportamiento estandar de django
        return super().form_valid(form)

    # aqui agrego el titulo y el numero de movimientos que se perderan al eliminar
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto de la confirmacion
        contexto = super().get_context_data(**kwargs)
        # aqui indico el titulo de la pagina de confirmacion
        contexto['titulo'] = f'Eliminar: {self.object.nombre}'
        # aqui cuento los movimientos que se borraran junto con el producto
        contexto['total_movimientos'] = self.object.movimientos.count()
        # aqui devuelvo el contexto a la plantilla
        return contexto


# aqui defino la vista de la coleccion global de movimientos con filtros
class VistaHistorialMovimientos(BaseInventarioView, ListView):
    # aqui defino el modelo de la coleccion de movimientos que se listara
    model = MovimientoStock
    # aqui indico la plantilla que dibuja la tabla del historial
    template_name = 'inventario/historial_movimientos.html'
    # aqui defino el nombre de la variable que recibe la coleccion en la plantilla
    context_object_name = 'movimientos'
    # aqui defino cuantos movimientos se muestran por pagina
    paginate_by = 20

    # aqui armo el formulario de filtros con los datos que envio el usuario
    def get_form(self):
        # aqui construyo el formulario pasando los parametros recibidos por la url
        return FiltroMovimientosForm(data=self.request.GET or None)

    # aqui entrego al selector el historial ya filtrado por texto y por tipo
    def get_queryset(self):
        # aqui leo el texto del buscador del historial
        query = self.request.GET.get('query', '').strip()
        # aqui leo el tipo de movimiento seleccionado en el filtro
        tipo = self.request.GET.get('tipo', '').strip()
        # aqui entrego al selector la coleccion con esos filtros aplicados
        return historial_movimientos(query=query, tipo=tipo)

    # aqui agrego al contexto los filtros activos y el formulario ya enlazado
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto de la lista paginada
        contexto = super().get_context_data(**kwargs)
        # aqui agrego el titulo de la pagina de historial
        contexto['titulo'] = 'Historial de movimientos'
        # aqui entrego el formulario de filtros ya validado
        contexto['form'] = self.get_form()
        # aqui entrego el total de movimientos antes de paginar
        contexto['total_resultados'] = self.get_queryset().count()
        # aqui devuelvo el contexto completo a la plantilla
        return contexto


# aqui defino la vista de la coleccion de categorias con su conteo de productos
class VistaListaCategorias(BaseInventarioView, ListView):
    # aqui defino el modelo de la coleccion de categorias
    model = Categoria
    # aqui indico la plantilla que dibuja la tabla de categorias
    template_name = 'inventario/lista_categorias.html'
    # aqui defino el nombre de la variable que recibe la coleccion en la plantilla
    context_object_name = 'categorias'
    # aqui defino el titulo de la pagina de categorias
    titulo_pagina = 'Categorías'

    # aqui uso el selector que anota el conteo de productos de cada categoria
    def get_queryset(self):
        # aqui entrego la coleccion de categorias ya anotada con su total de productos
        return categorias_con_conteo()

    # aqui defino el titulo visible en el encabezado de la pagina
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto de la lista
        contexto = super().get_context_data(**kwargs)
        # aqui agrego el titulo de la pagina de categorias
        contexto['titulo'] = 'Categorías'
        # aqui agrego el total de categorias registradas
        contexto['total_categorias'] = Categoria.objects.count()
        # aqui devuelvo el contexto completo a la plantilla
        return contexto


# aqui defino la vista de alta de una categoria nueva
class VistaCrearCategoria(RolRequeridoMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    # aqui defino el modelo que se creara
    model = Categoria
    # aqui uso el formulario de categoria con validacion de nombre unico
    form_class = CategoriaForm
    # aqui indico la plantilla que dibuja el formulario
    template_name = 'inventario/form_categoria.html'
    # aqui defino la pagina de destino despues de crear la categoria
    success_url = reverse_lazy('lista_categorias')
    # aqui limito el acceso a administradores y bodegueros
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui escribo el mensaje de exito de la operacion
    success_message = 'Categoría creada correctamente.'

    # aqui registro en el log que usuario creo la categoria
    def form_valid(self, form):
        # aqui asigno la cuenta que esta creando la categoria
        form.instance.creado_por = self.request.user
        # aqui delego el guardado al comportamiento estandar del formulario
        return super().form_valid(form)

    # aqui agrego el titulo de la pagina de alta de categoria
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto del formulario
        contexto = super().get_context_data(**kwargs)
        # aqui indico el titulo visible en la pagina
        contexto['titulo'] = 'Nueva categoría'
        # aqui devuelvo el contexto a la plantilla
        return contexto


# aqui defino la vista de edicion de una categoria existente
class VistaEditarCategoria(RolRequeridoMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    # aqui defino el modelo que se va a modificar
    model = Categoria
    # aqui uso el mismo formulario de alta para la edicion
    form_class = CategoriaForm
    # aqui indico la plantilla compartida de alta y edicion
    template_name = 'inventario/form_categoria.html'
    # aqui defino la pagina de destino despues de guardar
    success_url = reverse_lazy('lista_categorias')
    # aqui limito el acceso a administradores y bodegueros
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR, PerfilUsuario.BODEGUERO]
    # aqui escribo el mensaje de exito de la operacion
    success_message = 'Categoría actualizada correctamente.'

    # aqui agrego el titulo con el nombre de la categoria en edicion
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto del formulario
        contexto = super().get_context_data(**kwargs)
        # aqui armo el titulo descriptivo de la pagina
        contexto['titulo'] = f'Editar: {self.object.nombre}'
        # aqui devuelvo el contexto a la plantilla
        return contexto


# aqui defino la vista de eliminacion de categoria controlando la integridad referencial
class VistaEliminarCategoria(RolRequeridoMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    # aqui defino el modelo que se va a eliminar
    model = Categoria
    # aqui indico la plantilla de confirmacion con advertencias
    template_name = 'inventario/eliminar_categoria.html'
    # aqui defino la pagina de destino despues de eliminar el registro
    success_url = reverse_lazy('lista_categorias')
    # aqui limito el borrado solo a administradores del sistema
    roles_permitidos = [PerfilUsuario.ADMINISTRADOR]
    # aqui escribo el mensaje de exito de la operacion
    success_message = 'Categoría eliminada correctamente.'

    # aqui capturo el error de integridad referencial para explicar el motivo del rechazo
    def form_valid(self, form):
        # aqui guardo el nombre de la categoria antes de intentar borrarla
        nombre = self.object.nombre
        # aqui capturo el error especifico que django lanza cuando la categoria esta en uso
        try:
            # aqui delego el borrado real al comportamiento estandar de django
            return super().form_valid(form)
        except ProtectedError:
            # aqui aviso al usuario que no se puede borrar una categoria con productos
            messages.error(
                self.request,
                f'No se puede eliminar "{nombre}" porque tiene productos asociados. '
                'Desasigna o elimina esos productos primero.',
            )
            # aqui redirijo de vuelta a la coleccion de categorias
            return redirect('lista_categorias')

    # aqui agrego el titulo y la cantidad de productos que bloquean el borrado
    def get_context_data(self, **kwargs):
        # aqui llamo al metodo original para obtener el contexto de la confirmacion
        contexto = super().get_context_data(**kwargs)
        # aqui indico el titulo de la pagina de confirmacion
        contexto['titulo'] = f'Eliminar: {self.object.nombre}'
        # aqui cuento los productos que impiden eliminar la categoria
        contexto['total_productos'] = self.object.total_productos
        # aqui devuelvo el contexto a la plantilla
        return contexto


# aqui defino la vista que procesa la activacion o desactivacion masiva desde el catalogo
class VistaAccionMasiva(LoginRequiredMixin, View):
    # aqui defino el nombre de la plantilla usada cuando la peticion no llega por post
    template_name = 'inventario/lista_productos.html'

    # aqui valido la peticion y ejecuto la accion solicitada por el usuario
    def post(self, request, *args, **kwargs):
        # aqui leo la accion elegida en las casillas de seleccion multiple del catalogo
        accion = request.POST.get('accion', '')
        # aqui leo la lista de identificadores de productos marcados por el usuario
        lista_ids = request.POST.getlist('productos')
        # aqui si el usuario no marco ninguna fila le aviso y devuelvo el catalogo
        if not lista_ids:
            # aqui informo que la accion masiva no se puede ejecutar sin seleccion
            messages.error(request, 'Selecciona al menos un producto para aplicar la acción.')
            # aqui redirijo de vuelta al catalogo con los datos intactos
            return redirect('lista_productos')
        # aqui traduzco los identificadores a enteros para poder consultar la base
        ids_convertidos = [int(valor) for valor in lista_ids if valor.isdigit()]
        # aqui cargo la coleccion de productos correspondiente a la seleccion
        productos = Producto.objects.filter(pk__in=ids_convertidos)
        # aqui ejecuto la accion de desactivacion solicitada por el usuario
        if accion == 'desactivar':
            # aqui uso el servicio transaccional que desactiva el lote completo
            total = desactivar_productos(productos, usuario=request.user)
            # aqui confirmo al usuario cuantos productos fueron desactivados
            messages.success(request, f'{total} producto(s) marcado(s) como descontinuado(s).')
        # aqui ejecuto la accion de activacion solicitada por el usuario
        elif accion == 'activar':
            # aqui uso el servicio transaccional que reactiva el lote completo
            total = activar_productos(productos, usuario=request.user)
            # aqui confirmo al usuario cuantos productos fueron reactivados
            messages.success(request, f'{total} producto(s) reactivado(s) en el catálogo.')
        # aqui si la accion no existe en la lista blanca no ejecuto nada
        else:
            # aqui aviso al usuario que la accion solicitada no esta disponible
            messages.error(request, 'La acción solicitada no está disponible.')
        # aqui redirijo de vuelta al catalogo para ver el resultado de la accion
        return redirect('lista_productos')
