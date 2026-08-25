const parametros = new URLSearchParams(window.location.search);
document.getElementById('input-q').value = parametros.get('q') || '';
document.getElementById('select-categoria').value = parametros.get('categoria') || '';

const selectCategoria = document.getElementById('select-categoria');
StockFlow.listarCategorias().forEach(c => {
  const opcion = document.createElement('option');
  opcion.value = c.id;
  opcion.textContent = c.nombre;
  selectCategoria.appendChild(opcion);
});

function renderTabla() {
  const query = document.getElementById('input-q').value.toLowerCase();
  const categoriaId = document.getElementById('select-categoria').value;
  let productos = StockFlow.listarProductos();

  // Estructura condicional: mismos filtros que en la versión Django
  if (query) {
    productos = productos.filter(p =>
      p.nombre.toLowerCase().includes(query) || p.sku.toLowerCase().includes(query)
    );
  }
  if (categoriaId) {
    productos = productos.filter(p => p.categoriaId === Number(categoriaId));
  }

  const cuerpo = document.getElementById('cuerpo-tabla');
  if (!productos.length) {
    cuerpo.innerHTML = `
      <tr><td colspan="7" class="text-center text-muted py-4">
        No se encontraron productos.</td></tr>`;
    return;
  }

  cuerpo.innerHTML = productos.map(p => {
    const categoria = StockFlow.obtenerCategoria(p.categoriaId);
    const estado = p.stock <= p.stockMinimo
      ? '<span class="badge text-bg-warning">Reponer</span>'
      : '<span class="badge text-bg-success">OK</span>';
    return `
      <tr>
        <td><code>${p.sku}</code></td>
        <td>${p.nombre}</td>
        <td>${categoria ? categoria.nombre : '—'}</td>
        <td>${StockFlow.formatearMoneda(p.precio)}</td>
        <td>${p.stock} ${p.unidadMedida}</td>
        <td>${estado}${p.activo ? '' : ' <span class="badge text-bg-secondary">Inactivo</span>'}</td>
        <td class="text-end">
          <a href="producto.html?id=${p.id}" class="btn btn-sm btn-outline-primary">Ver</a>
          <a href="formulario.html?id=${p.id}" class="btn btn-sm btn-outline-secondary">Editar</a>
          <button class="btn btn-sm btn-outline-danger" data-eliminar="${p.id}">Eliminar</button>
        </td>
      </tr>`;
  }).join('');
}

document.getElementById('form-filtros').addEventListener('submit', e => {
  e.preventDefault();
  renderTabla();
});

document.getElementById('cuerpo-tabla').addEventListener('click', e => {
  const boton = e.target.closest('[data-eliminar]');
  if (!boton) return;

  const producto = StockFlow.obtenerProducto(boton.dataset.eliminar);
  if (confirm(`¿Eliminar "${producto.nombre}"? Esta acción no se puede deshacer.`)) {
    StockFlow.eliminarProducto(producto.id);
    mostrarAlerta(`Producto "${producto.nombre}" eliminado.`, 'success');
    renderTabla();
  }
});

function mostrarAlerta(mensaje, tipo) {
  const contenedor = document.getElementById('alerta-contenedor');
  contenedor.innerHTML = `
    <div class="alert alert-${tipo} alert-dismissible fade show">
      ${mensaje}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

renderTabla();
