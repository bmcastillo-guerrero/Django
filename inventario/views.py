# aqui importo el sistema de mensajes para dar avisos visuales al usuario
from django.contrib import messages
# aqui importo Q para poder realizar busquedas avanzadas con operador OR
from django.db.models import Q
# aqui importo los atajos clasicos de django para renderizar redireccionar y manejar 404
from django.shortcuts import get_object_or_404, redirect, render

# aqui importo los formularios de producto y movimiento
from .forms import MovimientoForm, ProductoForm
# aqui importo los modelos de datos que voy a consultar
from .models import Categoria, MovimientoStock, Producto


# aqui defino la vista del panel principal o dashboard con las metricas del negocio
def dashboard(request):
    # aqui rescato todos los productos activos de la base de datos
    productos = Producto.objects.filter(activo=True)
    # aqui calculo la cantidad total de productos registrados
    total_productos = productos.count()
    # aqui sumo las unidades totales en stock recorriendo los productos
    total_unidades = sum(p.stock for p in productos)
    # aqui calculo el valor monetario acumulado del inventario
    valor_inventario = sum(p.valor_inventario for p in productos)
    # aqui filtro los productos que necesitan reposicion segun su stock minimo
    por_reponer = [p for p in productos if p.necesita_reposicion]
    # aqui traigo todas las categorias existentes
    categorias = Categoria.objects.all()
    # aqui traigo los ultimos 8 movimientos optimizando la consulta con select_related
    ultimos_movimientos = MovimientoStock.objects.select_related('producto')[:8]

    # aqui armo el diccionario de contexto que se enviara a la plantilla
    contexto = {
        'total_productos': total_productos,
        'total_unidades': total_unidades,
        'valor_inventario': valor_inventario,
        'por_reponer': por_reponer,
        'categorias': categorias,
        'ultimos_movimientos': ultimos_movimientos,
    }
    # aqui renderizo la plantilla dashboard enviando el request y el contexto
    return render(request, 'inventario/dashboard.html', contexto)


# aqui defino la vista del catalogo de productos con buscador y filtro de categoria
def lista_productos(request):
    # aqui capturo el texto del buscador que viene por GET en el parametro q
    query = request.GET.get('q', '').strip()
    # aqui capturo la categoria seleccionada en los filtros que viene en categoria
    categoria_id = request.GET.get('categoria', '').strip()

    # aqui inicio la consulta trayendo los productos junto a su categoria con select_related
    productos = Producto.objects.select_related('categoria')

    # aqui aplico el filtro si el usuario escribio un texto en el buscador
    if query:
        # aqui uso el operador Q para buscar coincidencias en el nombre o en el sku sin distinguir mayusculas
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(sku__icontains=query)
        )
    # aqui aplico el filtro si el usuario selecciono una categoria especifica
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # aqui rescato todas las categorias para renderizar los botones de filtro
    categorias = Categoria.objects.all()
    # aqui renderizo la plantilla lista_productos con los datos filtrados
    return render(request, 'inventario/lista_productos.html', {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id,
    })


# aqui defino la vista para ver el detalle de un producto y registrar movimientos
def detalle_producto(request, pk):
    # aqui busco el producto por su clave primaria o arrojo error 404 si no existe
    producto = get_object_or_404(Producto, pk=pk)
    # aqui traigo los ultimos 20 movimientos del historial de este producto
    movimientos = producto.movimientos.all()[:20]

    # aqui verifico si el usuario envio el formulario por metodo POST
    if request.method == 'POST':
        # aqui enlazo los datos recibidos al formulario pasando el producto inicial
        form = MovimientoForm(request.POST, initial={'producto': producto})
        # aqui valido los datos en el servidor
        if form.is_valid():
            # aqui creo la instancia del movimiento sin guardarla aun en la base de datos
            movimiento = form.save(commit=False)
            # aqui asigno el producto correspondiente al movimiento
            movimiento.producto = producto

            # aqui aplico la regla condicional para actualizar el stock segun sea entrada o salida
            if movimiento.tipo == 'ENTRADA':
                # aqui sumo las unidades al stock si es una entrada
                producto.stock += movimiento.cantidad
            else:
                # aqui resto las unidades al stock si es una salida
                producto.stock -= movimiento.cantidad

            # aqui guardo los cambios en el producto y en el registro del movimiento
            producto.save()
            movimiento.save()
            # aqui genero un mensaje de exito para informar al usuario
            messages.success(request, f'Movimiento registrado en {producto.nombre}.')
            # aqui redirijo al detalle del producto para evitar reenvios del formulario
            return redirect('detalle_producto', pk=producto.pk)
    else:
        # aqui entrego el formulario vacio si la peticion es GET
        form = MovimientoForm(initial={'producto': producto})

    # aqui renderizo la plantilla de detalle con el producto el historial y el formulario
    return render(request, 'inventario/detalle_producto.html', {
        'producto': producto,
        'movimientos': movimientos,
        'form': form,
    })


# aqui defino la vista para crear un nuevo producto en el catalogo
def crear_producto(request):
    # aqui compruebo si la solicitud se envio por POST
    if request.method == 'POST':
        # aqui cargo los datos enviados en el formulario de producto
        form = ProductoForm(request.POST)
        # aqui valido que los campos cumplan las reglas del modelo
        if form.is_valid():
            # aqui guardo el nuevo producto en la base de datos
            producto = form.save()
            # aqui notifico al usuario con un mensaje de confirmacion
            messages.success(request, f'Producto "{producto.nombre}" creado.')
            # aqui redirijo a la lista general de productos
            return redirect('lista_productos')
    else:
        # aqui creo una instancia del formulario limpio para peticiones GET
        form = ProductoForm()

    # aqui renderizo la plantilla con el formulario de creacion
    return render(request, 'inventario/form_producto.html', {
        'form': form,
        'titulo': 'Nuevo producto',
    })


# aqui defino la vista para editar un producto existente
def editar_producto(request, pk):
    # aqui busco el producto a editar mediante su clave primaria
    producto = get_object_or_404(Producto, pk=pk)

    # aqui reviso si se enviaron cambios mediante el metodo POST
    if request.method == 'POST':
        # aqui vinculo los datos recibidos a la instancia actual del producto
        form = ProductoForm(request.POST, instance=producto)
        # aqui valido las modificaciones en el servidor
        if form.is_valid():
            # aqui guardo los cambios actualizados en la base de datos
            form.save()
            # aqui envio el mensaje de actualizacion exitosa
            messages.success(request, f'Producto "{producto.nombre}" actualizado.')
            # aqui redirijo al listado de productos
            return redirect('lista_productos')
    else:
        # aqui cargo el formulario con los datos actuales del producto para mostrar en pantalla
        form = ProductoForm(instance=producto)

    # aqui renderizo la plantilla reutilizando el formulario de edicion
    return render(request, 'inventario/form_producto.html', {
        'form': form,
        'titulo': f'Editar: {producto.nombre}',
    })


# aqui defino la vista para eliminar un producto con confirmacion previa
def eliminar_producto(request, pk):
    # aqui busco el producto que se desea eliminar
    producto = get_object_or_404(Producto, pk=pk)

    # aqui compruebo si se confirmo la eliminacion mediante POST
    if request.method == 'POST':
        # aqui guardo el nombre para incluirlo en el mensaje final
        nombre = producto.nombre
        # aqui ejecuto el borrado en la base de datos
        producto.delete()
        # aqui muestro el aviso de que el registro fue borrado
        messages.success(request, f'Producto "{nombre}" eliminado.')
        # aqui redirijo de vuelta al listado de productos
        return redirect('lista_productos')

    # aqui muestro la plantilla de confirmacion si la peticion es GET
    return render(request, 'inventario/eliminar_producto.html', {'producto': producto})
