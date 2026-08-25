const parametros = new URLSearchParams(window.location.search);
const idProducto = parametros.get('id');
const productoEditar = idProducto ? StockFlow.obtenerProducto(idProducto) : null;

if (productoEditar) {
  document.getElementById('titulo-formulario').textContent = `Editar: ${productoEditar.nombre}`;
  document.getElementById('campo-nombre').value = productoEditar.nombre;
  document.getElementById('campo-sku').value = productoEditar.sku;
  document.getElementById('campo-categoria').value = productoEditar.categoriaId;
  document.getElementById('campo-precio').value = productoEditar.precio;
  document.getElementById('campo-stock').value = productoEditar.stock;
  document.getElementById('campo-stock-minimo').value = productoEditar.stockMinimo;
  document.getElementById('campo-unidad').value = productoEditar.unidadMedida;
  document.getElementById('campo-activo').checked = productoEditar.activo;
}

const selectCategoria = document.getElementById('campo-categoria');
StockFlow.listarCategorias().forEach(c => {
  const opcion = document.createElement('option');
  opcion.value = c.id;
  opcion.textContent = c.nombre;
  selectCategoria.appendChild(opcion);
});
if (productoEditar) {
  selectCategoria.value = productoEditar.categoriaId;
}

document.getElementById('form-producto').addEventListener('submit', e => {
  e.preventDefault();
  const form = e.target;

  // Validación de campos obligatorios con estilos Bootstrap
  if (!form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }

  const nombre = document.getElementById('campo-nombre').value.trim();
  const sku = document.getElementById('campo-sku').value.trim().toUpperCase();

  // Regla de negocio: el SKU debe ser único (como unique=True en Django)
  const skuDuplicado = StockFlow.listarProductos()
    .some(p => p.sku === sku && p.id !== (productoEditar ? productoEditar.id : null));
  if (skuDuplicado) {
    alert(`El SKU "${sku}" ya existe en el inventario.`);
    return;
  }

  const datos = {
    id: productoEditar ? productoEditar.id : null,
    nombre,
    sku,
    categoriaId: Number(selectCategoria.value),
    precio: Number(document.getElementById('campo-precio').value),
    stock: Number(document.getElementById('campo-stock').value),
    stockMinimo: Number(document.getElementById('campo-stock-minimo').value),
    unidadMedida: document.getElementById('campo-unidad').value,
    activo: document.getElementById('campo-activo').checked,
  };

  if (!productoEditar && datos.stock > 0) {
    // Un producto nuevo con stock inicial genera su movimiento de ENTRADA
    StockFlow.guardarProducto(datos);
    window.location.href = 'productos.html';
    return;
  }

  StockFlow.guardarProducto(datos);
  window.location.href = 'productos.html';
});
