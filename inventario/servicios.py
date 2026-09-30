# aqui importo las transacciones de django para agrupar escrituras atomicas en la base de datos
from django.db import transaction
# aqui importo los modelos de inventario que concentran las reglas de negocio
from .models import MovimientoStock, Producto
# aqui importo mis errores de negocio para conversar con la capa de presentacion
from .excepciones import MovimientoInvalidoError, ProductoInactivoError, StockInsuficienteError
# aqui importo el logger del proyecto para auditar los cambios de inventario
import logging

# aqui creo el logger propio de la capa de servicios
logger = logging.getLogger('stockflow.inventario')


# aqui defino el servicio que registra una entrada o salida de mercaderia de forma segura
@transaction.atomic
def registrar_movimiento(*, producto, tipo, cantidad, observacion='', usuario=None):
    # aqui bloqueo la fila del producto para evitar que dos usuarios muevan stock a la vez
    producto_bloqueado = Producto.objects.select_for_update().get(pk=producto.pk)
    # aqui valido que la cantidad sea un numero entero positivo
    if not isinstance(cantidad, int) or cantidad < 1:
        # aqui lanzo el error de negocio con la razon del rechazo
        raise MovimientoInvalidoError('La cantidad debe ser un número entero mayor o igual a 1.')
    # aqui valido que el tipo de movimiento sea uno de los permitidos por el modelo
    if tipo not in dict(MovimientoStock.TIPOS):
        # aqui lanzo el error de negocio indicando el tipo invalido
        raise MovimientoInvalidoError('El tipo de movimiento no es válido.')
    # aqui valido que el producto siga activo en el catalogo
    if not producto_bloqueado.activo:
        # aqui lanzo el error de producto inactivo para que la vista lo muestre
        raise ProductoInactivoError(producto_bloqueado)
    # aqui valido que la salida no deje el stock en negativo
    if tipo == 'SALIDA' and cantidad > producto_bloqueado.stock:
        # aqui lanzo el error de stock insuficiente con los datos reales
        raise StockInsuficienteError(
            producto_bloqueado, producto_bloqueado.stock, cantidad
        )
    # aqui aplico la regla de negocio sumando o restando segun el tipo de movimiento
    if tipo == 'ENTRADA':
        # aqui sumo las unidades al stock actual del producto
        producto_bloqueado.stock += cantidad
    else:
        # aqui descuento las unidades del stock actual del producto
        producto_bloqueado.stock -= cantidad
    # aqui guardo el stock actualizado del producto
    producto_bloqueado.save(update_fields=['stock', 'actualizado_en'])
    # aqui creo el registro historico del movimiento ya con el usuario responsable
    movimiento = MovimientoStock.objects.create(
        producto=producto_bloqueado,
        tipo=tipo,
        cantidad=cantidad,
        observacion=observacion[:200],
        registrado_por=usuario if usuario is not None and usuario.is_authenticated else None,
    )
    # aqui dejo traza en el archivo de registros de quien movio que producto
    logger.info(
        'Movimiento %s de %s unidades sobre %s por %s',
        tipo,
        cantidad,
        producto_bloqueado.sku,
        getattr(usuario, 'username', 'sistema'),
    )
    # aqui devuelvo el movimiento creado para que la vista muestre el resultado
    return movimiento


# aqui defino el servicio que desactiva varios productos en una sola operacion
@transaction.atomic
def desactivar_productos(productos, usuario=None):
    # aqui obtengo solo los identificadores de la coleccion recibida para evitar objetos repetidos
    lista_ids = [producto.pk for producto in productos]
    # aqui actualizo todos los productos desactivados en una sola consulta de base de datos
    actualizados = Producto.objects.filter(pk__in=lista_ids).update(activo=False)
    # aqui registro en el log la accion masiva realizada
    logger.info(
        'Desactivación masiva de %s productos por %s',
        actualizados,
        getattr(usuario, 'username', 'sistema'),
    )
    # aqui devuelvo la cantidad de filas realmente afectadas
    return actualizados


# aqui defino el servicio que reactiva varios productos seleccionados en el panel
@transaction.atomic
def activar_productos(productos, usuario=None):
    # aqui obtengo solo los identificadores de la coleccion recibida
    lista_ids = [producto.pk for producto in productos]
    # aqui actualizo todos los productos como activos en una sola consulta
    actualizados = Producto.objects.filter(pk__in=lista_ids).update(activo=True)
    # aqui registro en el log la accion masiva realizada
    logger.info(
        'Reactivación masiva de %s productos por %s',
        actualizados,
        getattr(usuario, 'username', 'sistema'),
    )
    # aqui devuelvo la cantidad de filas realmente afectadas
    return actualizados


# aqui defino el servicio que ajusta el stock de forma directa sin generar movimiento
@transaction.atomic
def ajustar_stock(producto, nuevo_stock, usuario=None):
    # aqui valido que el nuevo stock sea un entero valido
    if not isinstance(nuevo_stock, int) or nuevo_stock < 0:
        # aqui lanzo el error de movimiento invalido explicando el problema
        raise MovimientoInvalidoError('El stock no puede ser un número negativo.')
    # aqui bloqueo la fila para que el ajuste sea coherente con movimientos simultaneos
    producto_bloqueado = Producto.objects.select_for_update().get(pk=producto.pk)
    # aqui registro el valor anterior para poder dejar traza del cambio
    stock_anterior = producto_bloqueado.stock
    # aqui asigno el nuevo valor de stock al producto bloqueado
    producto_bloqueado.stock = nuevo_stock
    # aqui guardo solo los campos que cambiaron para optimizar la escritura
    producto_bloqueado.save(update_fields=['stock', 'actualizado_en'])
    # aqui dejo constancia del ajuste directo en el archivo de registros
    logger.info(
        'Ajuste manual de stock de %s: %s -> %s por %s',
        producto_bloqueado.sku,
        stock_anterior,
        nuevo_stock,
        getattr(usuario, 'username', 'sistema'),
    )
    # aqui devuelvo el producto ya guardado con el stock nuevo
    return producto_bloqueado
