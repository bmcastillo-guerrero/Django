from django.db import models
from django.core.validators import MinValueValidator


class Categoria(models.Model):
    """Categoría que agrupa productos del inventario."""

    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def total_productos(self):
        """Operación de conteo: cantidad de productos de la categoría."""
        return self.productos.count()


class Producto(models.Model):
    """Producto registrado en el inventario de la tienda."""

    UNIDADES = [
        ('UN', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('LT', 'Litro'),
        ('PAQ', 'Paquete'),
    ]

    nombre = models.CharField(max_length=120)
    sku = models.CharField(max_length=20, unique=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    unidad_medida = models.CharField(max_length=3, choices=UNIDADES, default='UN')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.nombre} ({self.sku})'

    @property
    def necesita_reposicion(self):
        """Operación de comparación: indica si hay que reponer stock."""
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self):
        """Operación aritmética: valor total del stock del producto."""
        return self.precio * self.stock


class MovimientoStock(models.Model):
    """Entrada o salida de stock asociada a un producto."""

    TIPOS = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos',
    )
    tipo = models.CharField(max_length=7, choices=TIPOS)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    observacion = models.CharField(max_length=200, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'movimientos de stock'

    def __str__(self):
        return f'{self.tipo} {self.cantidad} - {self.producto.nombre}'
