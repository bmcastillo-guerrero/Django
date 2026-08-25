const idProducto = new URLSearchParams(window.location.search).get('id');
const producto = StockFlow.obtenerProducto(idProducto);

if (!producto) {
  document.getElementById('producto-no-encontrado').classList.remove('d-none');
} else {
  document.getElementById('contenido-producto').classList.remove('d-none');

  const categoria = StockFlow.obtenerCategoria(producto.categoriaId);

  document.getElementById('migaja-nombre').textContent = producto.nombre;
  document.getElementById('detalle-nombre').textContent = producto.nombre;
  document.getElementById('detalle-sku').textContent = producto.sku;
  document.getElementById('detalle-categoria').textContent = categoria ? categoria.nombre : '—';
  document.getElementById('boton-editar').href = `formulario.html?id=${producto.id}`;

  function renderDetalle() {
    const estado = producto.stock <= producto.stockMinimo
      ? '<span class="badge text-bg-warning">Necesita reposición</span>'
      : '<span class="badge text-bg-success">OK</span>';

    document.getElementById('detalle-datos').innerHTML = `
      <li><strong>Precio:</strong> ${StockFlow.formatearMoneda(producto.precio)}</li>
      <li><strong>Stock actual:</strong> ${producto.stock} ${producto.unidadMedida}</li>
      <li><strong>Stock mínimo:</strong> ${producto.stockMinimo}</li>
      <li><strong>Valor en inventario:</strong>
        ${StockFlow.formatearMoneda(producto.precio * producto.stock)}</li>
      <li><strong>Estado:</strong> ${estado}</li>`;
    document.getElementById('boton-eliminar').dataset.id = producto.id;
  }

  function renderHistorial() {
    const movimientos = StockFlow.listarMovimientos(producto.id);
    const tabla = document.getElementById('tabla-historial');
    const vacio = document.getElementById('sin-historial');

    if (movimientos.length) {
      tabla.classList.remove('d-none');
      tabla.querySelector('tbody').innerHTML = movimientos.map(m => {
        const badge = m.tipo === 'ENTRADA' ? 'text-bg-success' : 'text-bg-secondary';
        return `
          <tr>
            <td>${StockFlow.formatearFecha(m.fecha)}</td>
            <td><span class="badge ${badge}">${m.tipo}</span></td>
            <td>${m.cantidad}</td>
            <td>${m.observacion || '—'}</td>
          </tr>`;
      }).join('');
    } else {
      vacio.classList.remove('d-none');
    }
  }

  document.getElementById('form-movimiento').addEventListener('submit', e => {
    e.preventDefault();
    const tipo = document.getElementById('mov-tipo').value;
    const cantidad = Number(document.getElementById('mov-cantidad').value);
    const observacion = document.getElementById('mov-observacion').value.trim();
    const alerta = document.getElementById('alerta-movimiento');

    if (!cantidad || cantidad < 1) {
      alerta.innerHTML = '<div class="alert alert-danger">La cantidad debe ser mayor a 0.</div>';
      return;
    }

    const resultado = StockFlow.registrarMovimiento(producto.id, tipo, cantidad, observacion);
    if (resultado.error) {
      alerta.innerHTML = `<div class="alert alert-danger">${resultado.error}</div>`;
      return;
    }

    // Refrescar datos del producto tras el movimiento
    Object.assign(producto, StockFlow.obtenerProducto(producto.id));
    alerta.innerHTML = `<div class="alert alert-success">Movimiento registrado.</div>`;
    renderDetalle();
    renderHistorial();
    e.target.reset();
    document.getElementById('mov-cantidad').value = 1;
  });

  document.getElementById('boton-eliminar').addEventListener('click', () => {
    if (confirm(`¿Eliminar "${producto.nombre}"? También se borrará su historial.`)) {
      StockFlow.eliminarProducto(producto.id);
      window.location.href = 'productos.html';
    }
  });

  renderDetalle();
  renderHistorial();
}
