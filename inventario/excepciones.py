# aqui defino la jerarquia de errores de negocio para separar los fallos controlados
class ErrorNegocio(Exception):
    # aqui documento el modelo base que representa un fallo esperado de las reglas del sistema
    pass


# aqui defino el error que se lanza cuando una salida supera el stock disponible
class StockInsuficienteError(ErrorNegocio):
    # aqui inicializo el error guardando el producto y las unidades realmente disponibles
    def __init__(self, producto, disponibles, solicitadas):
        # aqui armo el mensaje de error con los datos reales del problema
        mensaje = (
            f'Solo hay {disponibles} unidades disponibles de "{producto.nombre}" '
            f'y se solicitaron {solicitadas}.'
        )
        # aqui inicializo la clase base con el mensaje construido
        super().__init__(mensaje)
        # aqui guardo el producto afectado para que la vista pueda usarlo
        self.producto = producto
        # aqui guardo el stock real que quedo sin modificar
        self.disponibles = disponibles
        # aqui guardo la cantidad que el usuario quiso mover
        self.solicitadas = solicitadas


# aqui defino el error que se lanza cuando se intenta mover un producto descontinuado
class ProductoInactivoError(ErrorNegocio):
    # aqui inicializo el error con el nombre del producto inactivo
    def __init__(self, producto):
        # aqui construyo el mensaje explicando que el producto esta descontinuado
        super().__init__(f'El producto "{producto.nombre}" está descontinuado y no admite movimientos.')
        # aqui guardo el producto rechazado
        self.producto = producto


# aqui defino el error que se lanza cuando la cantidad del movimiento no es valida
class MovimientoInvalidoError(ErrorNegocio):
    # aqui inicializo el error con la razon puntual del rechazo
    def __init__(self, razon):
        # aqui delego el mensaje al constructor de la clase base
        super().__init__(razon)
        # aqui guardo la razon para reutilizarla en el formulario
        self.razon = razon
