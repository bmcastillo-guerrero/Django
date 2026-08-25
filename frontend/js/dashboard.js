const metricas = StockFlow.metricas();

document.getElementById('metrica-productos').textContent = metricas.totalProductos;
document.getElementById('metrica-unidades').textContent = metricas.totalUnidades;
document.getElementById('metrica-valor').textContent = StockFlow.formatearMoneda(metricas.valorInventario);
document.getElementById('metrica-alertas').textContent = metricas.porReponer.length;

const listaAlertas = document.getElementById('lista-alertas');
if (metricas.porReponer.length) {
  listaAlertas.innerHTML = metricas.porReponer.map(p => `
    <div class="d-flex justify-content-between align-items-center border-bottom py-2">
      <div>${p.nombre} <code class="ms-1">${p.sku}</code></div>
      <span class="badge text-bg-warning">${p.stock} / mín ${p.stockMinimo}</span>
    </div>
  `).join('');
} else {
  listaAlertas.innerHTML = '<p class="text-muted mb-0">Todo el stock está sobre el mínimo. Sin alertas.</p>';
}

const movimientos = StockFlow.listarUltimosMovimientos();
const tabla = document.getElementById('tabla-movimientos');
const vacio = document.getElementById('sin-movimientos');
if (movimientos.length) {
  tabla.classList.remove('d-none');
  tabla.querySelector('tbody').innerHTML = movimientos.map(m => {
    const producto = StockFlow.obtenerProducto(m.productoId);
    const badge = m.tipo === 'ENTRADA' ? 'text-bg-success' : 'text-bg-secondary';
    return `
      <tr>
        <td>${producto ? producto.nombre : '—'}</td>
        <td><span class="badge ${badge}">${m.tipo}</span></td>
        <td>${m.cantidad}</td>
        <td>${StockFlow.formatearFecha(m.fecha)}</td>
      </tr>`;
  }).join('');
} else {
  vacio.classList.remove('d-none');
}

const categorias = StockFlow.listarCategorias();
const productos = StockFlow.listarProductos();
document.getElementById('lista-categorias').innerHTML = categorias.map(c => {
  const total = productos.filter(p => p.categoriaId === c.id).length;
  return `<a href="productos.html?categoria=${c.id}"
            class="badge text-bg-light border me-1 mb-1 text-decoration-none">
            ${c.nombre} (${total})</a>`;
}).join('');
