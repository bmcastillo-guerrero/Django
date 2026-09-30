# aqui importo las funciones de agregacion del orm para calcular metricas en la base de datos
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
# aqui importo la funcion coalesce que reemplaza el valor nulo por un cero en los agregados
from django.db.models.functions import Coalesce
# aqui importo el decimal para escribir el cero de respaldo con dos decimales
from decimal import Decimal

# aqui importo los modelos del inventario que se consultan en esta capa de solo lectura
from .models import Categoria, MovimientoStock, Producto

# aqui defino el tipo decimal con el que salen todos los agregados monetarios del inventario
CAMPO_DECIMAL = DecimalField(max_digits=14, decimal_places=2)


# aqui defino el helper que multiplica precio por stock resolviendo el tipo decimal
def valor_en_base(productos):
    # aqui envuelvo la multiplicacion porque django no puede inferir el tipo al mezclar campos
    # precio es decimal y stock es entero por eso la expresion necesita un output_field explicito
    return ExpressionWrapper(F('precio') * F('stock'), output_field=CAMPO_DECIMAL)


# aqui defino el mapa de ordenamientos permitidos para evitar inyeccion en el parametro de orden
ORDENES_PERMITIDOS = {
    'recientes': '-fecha_registro',
    'antiguos': 'fecha_registro',
    'nombre': 'nombre',
    'precio_asc': 'precio',
    'precio_desc': '-precio',
    'stock_asc': 'stock',
    'stock_desc': '-stock',
}


# aqui defino el selector que arma la coleccion de productos filtrada y ordenada
def productos_filtrados(query='', categoria_id=None, orden='recientes', incluir_inactivos=False):
    # aqui parto de la consulta base con la categoria ya cargada para evitar una consulta por producto
    productos = Producto.objects.select_related('categoria')
    # aqui excluyo los productos descontinuados salvo que se pidan explicitamente
    if not incluir_inactivos:
        productos = productos.filter(activo=True)
    # aqui aplico el buscador combinando nombre y sku con el operador logico or
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(sku__icontains=query)
        )
    # aqui aplico el filtro por categoria solo cuando se selecciono una en la interfaz
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    # aqui valido que el orden pedido pertenezca a la lista blanca y sino uso el valor por defecto
    campo_orden = ORDENES_PERMITIDOS.get(orden, ORDENES_PERMITIDOS['recientes'])
    # aqui devuelvo la coleccion ya filtrada y ordenada segun el parametro recibido
    return productos.order_by(campo_orden)


# aqui defino el selector que calcula todas las metricas del panel en una sola consulta
def metricas_dashboard():
    # aqui consulto los agregados usando sum count y max directamente en la base de datos
    totales = Producto.objects.filter(activo=True).aggregate(
        # aqui cuento la cantidad de productos activos usando count sobre el identificador
        total_productos=Count('id'),
        # aqui sumo el stock de todos los productos activos
        total_unidades=Coalesce(Sum('stock'), 0),
        # aqui multiplico precio por stock en la base de datos para obtener el valor del inventario
        valor_inventario=Coalesce(
            Sum(valor_en_base(Producto)),
            Value(Decimal('0.00')),
            output_field=CAMPO_DECIMAL,
        ),
    )
    # aqui consulto la cantidad total de movimientos registrados en el historial
    totales['total_movimientos'] = MovimientoStock.objects.count()
    # aqui devuelvo el diccionario con todas las metricas ya calculadas
    return totales


# aqui defino el selector que devuelve los productos que ya llegaron a su stock minimo
def productos_por_reponer(limite=None):
    # aqui uso unicamente las consultas anotadas porque el stock minimo vive en cada fila
    productos = Producto.objects.filter(activo=True, stock__lte=F('stock_minimo')).select_related('categoria')
    # aqui ordeno primero por mayor urgencia porque django no permite ordenar despues de cortar
    productos = productos.order_by('stock')
    # aqui limito la cantidad de resultados cuando la vista lo necesita para el panel
    if limite is not None:
        productos = productos[:limite]
    # aqui devuelvo la coleccion de productos en alerta ordenada por mayor urgencia
    return productos


# aqui defino el selector que construye el historial global de movimientos de la aplicacion
def historial_movimientos(query='', tipo=None, limite=None):
    # aqui parto de la consulta con el producto y su categoria ya relacionados
    movimientos = MovimientoStock.objects.select_related('producto', 'producto__categoria', 'registrado_por')
    # aqui filtro por tipo de movimiento cuando el usuario elige una opcion del filtro
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    # aqui filtro por texto libre buscando en el sku el nombre o la observacion
    if query:
        movimientos = movimientos.filter(
            Q(producto__sku__icontains=query)
            | Q(producto__nombre__icontains=query)
            | Q(observacion__icontains=query)
        )
    # aqui limito la cantidad de resultados cuando la vista lo necesita
    if limite is not None:
        movimientos = movimientos[:limite]
    # aqui devuelvo la coleccion de movimientos ya filtrada
    return movimientos


# aqui defino el selector que arma la coleccion de categorias con el conteo de productos
def categorias_con_conteo():
    # aqui uso la anotacion de django para contar los productos sin disparar una consulta por fila
    # la anotacion se llama productos_activos porque total_productos ya existe como propiedad
    # calculada del modelo y django no puede sobrescribir una propiedad sin setter
    return Categoria.objects.annotate(
        productos_activos=Count('productos', filter=Q(productos__activo=True))
    ).order_by('nombre')


# aqui defino el selector que entrega el valor total del inventario activo
def valor_inventario_activo():
    # aqui calculo el total monetario con una unica consulta agregada sobre los productos activos
    return Producto.objects.filter(activo=True).aggregate(
        total=Coalesce(
            Sum(valor_en_base(Producto)),
            Value(Decimal('0.00')),
            output_field=CAMPO_DECIMAL,
        )
    )['total']
