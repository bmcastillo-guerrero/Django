from django.contrib import admin

from .models import Categoria, MovimientoStock, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'total_productos')
    search_fields = ('nombre',)


class MovimientoStockInline(admin.TabularInline):
    model = MovimientoStock
    extra = 0


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'nombre',
        'categoria',
        'precio',
        'stock',
        'estado_stock',
    )
    list_filter = ('categoria', 'unidad_medida', 'activo')
    search_fields = ('nombre', 'sku')
    inlines = [MovimientoStockInline]

    @admin.display(description='Estado de stock')
    def estado_stock(self, obj):
        return 'Reponer' if obj.necesita_reposicion else 'OK'
