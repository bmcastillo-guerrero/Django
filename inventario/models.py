# aqui importo las herramientas de modelos y validadores de django
from django.db import models
from django.core.validators import MinValueValidator

# aqui defino la clase categoria para clasificar los productos del inventario
class Categoria(models.Model):
    # aqui defino el campo nombre que debe ser unico para evitar categorias repetidas
    nombre = models.CharField(max_length=80, unique=True)
    # aqui defino una descripcion opcional para detallar la categoria
    descripcion = models.TextField(blank=True)

    class Meta:
        # aqui configuro los nombres legibles en singular y plural
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        # aqui ordeno alfabeticamente por nombre
        ordering = ['nombre']

    # aqui defino la representacion en texto del objeto para mostrar su nombre
    def __str__(self):
        return self.nombre

    # aqui creo una propiedad calculada para contar cuantos productos tiene esta categoria
    @property
    def total_productos(self):
        # aqui ejecuto la operacion de conteo sobre la relacion inversa productos
        return self.productos.count()


# aqui defino la clase producto que representa cada articulo disponible en la tienda
class Producto(models.Model):
    # aqui defino las opciones fijas para las unidades de medida
    UNIDADES = [
        ('UN', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('LT', 'Litro'),
        ('PAQ', 'Paquete'),
    ]

    # aqui defino el nombre comercial del producto
    nombre = models.CharField(max_length=120)
    # aqui defino el codigo sku unico que identifica al producto en bodega
    sku = models.CharField(max_length=20, unique=True)
    # aqui relaciono el producto con una categoria usando clave foranea
    # uso on_delete PROTECT para impedir que se borre una categoria si tiene productos asignados
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
    )
    # aqui defino el precio usando DecimalField para asegurar precision monetaria sin errores de redondeo
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    # aqui almaceno las unidades disponibles actualmente en inventario
    stock = models.PositiveIntegerField(default=0)
    # aqui establezco el limite minimo de stock para activar la alerta de reposicion
    stock_minimo = models.PositiveIntegerField(default=5)
    # aqui defino la unidad de medida usando las opciones predefinidas
    unidad_medida = models.CharField(max_length=3, choices=UNIDADES, default='UN')
    # aqui guardo automaticamente la fecha y hora de registro del producto
    fecha_registro = models.DateTimeField(auto_now_add=True)
    # aqui indico si el producto esta activo o descontinuado
    activo = models.BooleanField(default=True)

    class Meta:
        # aqui ordeno los productos para que los mas recientes aparezcan primero
        ordering = ['-fecha_registro']

    # aqui retorno el nombre junto con el sku para identificarlo claramente
    def __str__(self):
        return f'{self.nombre} ({self.sku})'

    # aqui implemento la regla de negocio para saber si el producto necesita reposicion
    @property
    def necesita_reposicion(self):
        # aqui comparo si el stock actual es menor o igual al minimo permitido
        return self.stock <= self.stock_minimo

    # aqui calculo el valor total del inventario para este producto
    @property
    def valor_inventario(self):
        # aqui multiplico el precio unitario por la cantidad de unidades en bodega
        return self.precio * self.stock

    # aqui calculo el porcentaje de stock para alimentar la barra visual de la tarjeta
    @property
    def porcentaje_stock(self):
        # aqui aseguro un minimo si el stock minimo no esta configurado
        if not self.stock_minimo or self.stock_minimo <= 0:
            return 100
        # aqui tomo como referencia un stock optimo de tres veces el minimo
        meta = self.stock_minimo * 3
        calculo = int((self.stock / meta) * 100)
        # aqui limito el valor entre 5 y 100 para que la barra siempre sea visible
        return min(100, max(8, calculo))


# aqui defino la clase movimiento de stock para registrar entradas y salidas de mercaderia
class MovimientoStock(models.Model):
    # aqui defino los tipos de movimiento permitidos
    TIPOS = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]

    # aqui vinculo cada movimiento a un producto usando clave foranea
    # uso CASCADE para que si se elimina un producto su historial de movimientos se borre con el
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos',
    )
    # aqui guardo si el movimiento es una entrada o una salida
    tipo = models.CharField(max_length=7, choices=TIPOS)
    # aqui almaceno la cantidad asegurando que sea un valor mayor o igual a 1
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    # aqui guardo un comentario o motivo opcional del movimiento
    observacion = models.CharField(max_length=200, blank=True)
    # aqui registro la fecha y hora exacta del movimiento de forma automatica
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        # aqui ordeno para mostrar siempre los movimientos mas recientes primero
        ordering = ['-fecha']
        verbose_name_plural = 'movimientos de stock'

    # aqui defino la representacion en texto del movimiento
    def __str__(self):
        return f'{self.tipo} {self.cantidad} - {self.producto.nombre}'
