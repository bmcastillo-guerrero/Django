# aqui importo el modulo de administracion de django
from django.contrib import admin

# aqui importo los modelos del inventario para registrarlos
from .models import Categoria, MovimientoStock, Producto

# aqui personalizo los titulos del panel de control para que muestren la marca stockflow
admin.site.site_header = "StockFlow — Panel de Inventario"
admin.site.site_title = "StockFlow"
admin.site.index_title = "Gestión de Bodega y Productos"


# aqui registro y personalizo el modelo Categoria en el panel de administracion
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    # aqui defino las columnas visibles en la tabla del panel
    list_display = ('nombre', 'total_productos')
    # aqui agrego un buscador por el nombre de la categoria
    search_fields = ('nombre',)
    # aqui ordeno las categorias alfabeticamente
    ordering = ('nombre',)
    # aqui limito la cantidad de elementos por pagina
    list_per_page = 15


# aqui defino la clase tabular para incrustar el historial de movimientos dentro de cada producto
class MovimientoStockInline(admin.TabularInline):
    model = MovimientoStock
    extra = 0
    # aqui indico que los movimientos existentes se muestren en modo solo lectura
    readonly_fields = ('fecha',)


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
        'estado_stock',
    )
    # aqui agrego filtros laterales por categoria unidad y estado activo
    list_filter = ('categoria', 'unidad_medida', 'activo')
    # aqui habilito la barra de busqueda por nombre o sku
    search_fields = ('nombre', 'sku')
    # aqui incrusto los movimientos de stock en la misma pantalla del producto
    inlines = [MovimientoStockInline]
    # aqui ordeno para que los productos mas nuevos salgan primero
    ordering = ('-id',)
    # aqui configuro la paginacion profesional en el panel
    list_per_page = 15

    # aqui defino un metodo personalizado para mostrar visualmente el estado del stock
    @admin.display(description='Estado de stock')
    def estado_stock(self, obj):
        # aqui devuelvo si requiere reponer segun la propiedad calculada
        return 'Reponer' if obj.necesita_reposicion else 'OK'
