from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MovimientoForm, ProductoForm
from .models import Categoria, MovimientoStock, Producto


def dashboard(request):
    """Panel principal con resumen del inventario (lógica del lado del servidor)."""
    productos = Producto.objects.filter(activo=True)
    total_productos = productos.count()
    total_unidades = sum(p.stock for p in productos)
    valor_inventario = sum(p.valor_inventario for p in productos)
    por_reponer = [p for p in productos if p.necesita_reposicion]
    categorias = Categoria.objects.all()
    ultimos_movimientos = MovimientoStock.objects.select_related('producto')[:8]

    contexto = {
        'total_productos': total_productos,
        'total_unidades': total_unidades,
        'valor_inventario': valor_inventario,
        'por_reponer': por_reponer,
        'categorias': categorias,
        'ultimos_movimientos': ultimos_movimientos,
    }
    return render(request, 'inventario/dashboard.html', contexto)


def lista_productos(request):
    """Listado de productos con búsqueda y filtro por categoría."""
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')

    productos = Producto.objects.select_related('categoria')

    # Estructura condicional + operadores lógicos para filtrar según requerimiento
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(sku__icontains=query)
        )
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    categorias = Categoria.objects.all()
    return render(request, 'inventario/lista_productos.html', {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id,
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = producto.movimientos.all()[:20]

    if request.method == 'POST':
        form = MovimientoForm(request.POST, initial={'producto': producto})
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.producto = producto

            # Operador condicional: actualizar stock según el tipo de movimiento
            if movimiento.tipo == 'ENTRADA':
                producto.stock += movimiento.cantidad
            else:
                producto.stock -= movimiento.cantidad

            producto.save()
            movimiento.save()
            messages.success(request, f'Movimiento registrado en {producto.nombre}.')
            return redirect('detalle_producto', pk=producto.pk)
    else:
        form = MovimientoForm(initial={'producto': producto})

    return render(request, 'inventario/detalle_producto.html', {
        'producto': producto,
        'movimientos': movimientos,
        'form': form,
    })


def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()

    return render(request, 'inventario/form_producto.html', {
        'form': form,
        'titulo': 'Nuevo producto',
    })


def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/form_producto.html', {
        'form': form,
        'titulo': f'Editar: {producto.nombre}',
    })


def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado.')
        return redirect('lista_productos')

    return render(request, 'inventario/eliminar_producto.html', {'producto': producto})
