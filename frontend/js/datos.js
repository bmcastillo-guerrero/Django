/*
 * StockFlow - Capa de datos del frontend
 * Simula el backend con localStorage usando la misma estructura
 * de los modelos Django (Categoria, Producto, MovimientoStock).
 * Al conectar con la API REST de Django solo hay que reemplazar este archivo.
 */
const StockFlow = (() => {
  const CLAVE = 'stockflow_db';

  function datosSemilla() {
    const ahora = new Date().toISOString();
    return {
      categorias: [
        { id: 1, nombre: 'Abarrotes', descripcion: 'Productos alimenticios básicos' },
        { id: 2, nombre: 'Bebidas', descripcion: 'Agua, jugos, gaseosas' },
        { id: 3, nombre: 'Limpieza', descripcion: 'Artículos de aseo del hogar' },
        { id: 4, nombre: 'Snacks', descripcion: 'Colaciones y golosinas' },
        { id: 5, nombre: 'Cuidado personal', descripcion: 'Higiene y cuidado personal' },
      ],
      productos: [
        { id: 1, nombre: 'Arroz Grado 1', sku: 'SKU-1001-AB', categoriaId: 1, precio: 1250, stock: 80, stockMinimo: 10, unidadMedida: 'KG', activo: true, fechaRegistro: ahora },
        { id: 2, nombre: 'Fideos Coditos', sku: 'SKU-1002-AB', categoriaId: 1, precio: 990, stock: 45, stockMinimo: 10, unidadMedida: 'PAQ', activo: true, fechaRegistro: ahora },
        { id: 3, nombre: 'Aceite Vegetal 1L', sku: 'SKU-1003-AB', categoriaId: 1, precio: 3200, stock: 6, stockMinimo: 8, unidadMedida: 'LT', activo: true, fechaRegistro: ahora },
        { id: 4, nombre: 'Agua Mineral 6Pack', sku: 'SKU-2001-BB', categoriaId: 2, precio: 2800, stock: 30, stockMinimo: 5, unidadMedida: 'PAQ', activo: true, fechaRegistro: ahora },
        { id: 5, nombre: 'Gaseosa Cola 3LT', sku: 'SKU-2002-BB', categoriaId: 2, precio: 2450, stock: 0, stockMinimo: 6, unidadMedida: 'UN', activo: true, fechaRegistro: ahora },
        { id: 6, nombre: 'Detergente en Polvo', sku: 'SKU-3001-LM', categoriaId: 3, precio: 4100, stock: 22, stockMinimo: 5, unidadMedida: 'KG', activo: true, fechaRegistro: ahora },
        { id: 7, nombre: 'Papas Fritas Bolsa', sku: 'SKU-4001-SN', categoriaId: 4, precio: 850, stock: 110, stockMinimo: 15, unidadMedida: 'UN', activo: true, fechaRegistro: ahora },
        { id: 8, nombre: 'Jabón de Manos', sku: 'SKU-5001-CP', categoriaId: 5, precio: 1600, stock: 4, stockMinimo: 5, unidadMedida: 'UN', activo: false, fechaRegistro: ahora },
      ],
      movimientos: [
        { id: 1, productoId: 1, tipo: 'ENTRADA', cantidad: 50, observacion: 'Compra a proveedor central', fecha: ahora },
        { id: 2, productoId: 1, tipo: 'SALIDA', cantidad: 20, observacion: 'Venta mostrador', fecha: ahora },
        { id: 3, productoId: 5, tipo: 'SALIDA', cantidad: 12, observacion: 'Venta fin de semana', fecha: ahora },
      ],
    };
  }

  function leer() {
    const crudo = localStorage.getItem(CLAVE);
    if (!crudo) {
      const semilla = datosSemilla();
      localStorage.setItem(CLAVE, JSON.stringify(semilla));
      return semilla;
    }
    return JSON.parse(crudo);
  }

  function escribir(db) {
    localStorage.setItem(CLAVE, JSON.stringify(db));
  }

  function siguienteId(coleccion) {
    return coleccion.length ? Math.max(...coleccion.map(x => x.id)) + 1 : 1;
  }

  return {
    reiniciar() {
      localStorage.removeItem(CLAVE);
    },

    listarCategorias() {
      return leer().categorias;
    },

    obtenerCategoria(id) {
      return leer().categorias.find(c => c.id === Number(id));
    },

    listarProductos() {
      return leer().productos;
    },

    obtenerProducto(id) {
      return leer().productos.find(p => p.id === Number(id));
    },

    guardarProducto(datos) {
      const db = leer();
      if (datos.id) {
        const indice = db.productos.findIndex(p => p.id === datos.id);
        if (indice === -1) return null;
        db.productos[indice] = { ...db.productos[indice], ...datos };
      } else {
        datos.id = siguienteId(db.productos);
        datos.fechaRegistro = new Date().toISOString();
        db.productos.push(datos);
      }
      escribir(db);
      return datos;
    },

    eliminarProducto(id) {
      const db = leer();
      db.productos = db.productos.filter(p => p.id !== Number(id));
      db.movimientos = db.movimientos.filter(m => m.productoId !== Number(id));
      escribir(db);
    },

    listarMovimientos(productoId) {
      return leer().movimientos
        .filter(m => m.productoId === Number(productoId))
        .sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
    },

    listarUltimosMovimientos(limite = 8) {
      return leer().movimientos
        .slice()
        .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
        .slice(0, limite);
    },

    registrarMovimiento(productoId, tipo, cantidad, observacion) {
      const db = leer();
      const producto = db.productos.find(p => p.id === Number(productoId));
      if (!producto) return { error: 'Producto no encontrado.' };

      // Validación que replica la del servidor Django
      if (tipo === 'SALIDA' && cantidad > producto.stock) {
        return { error: `Solo hay ${producto.stock} unidades disponibles.` };
      }

      producto.stock += tipo === 'ENTRADA' ? cantidad : -cantidad;
      db.movimientos.push({
        id: siguienteId(db.movimientos),
        productoId: producto.id,
        tipo,
        cantidad,
        observacion,
        fecha: new Date().toISOString(),
      });
      escribir(db);
      return { ok: true };
    },

    metricas() {
      const productos = leer().productos.filter(p => p.activo);
      return {
        totalProductos: productos.length,
        totalUnidades: productos.reduce((suma, p) => suma + p.stock, 0),
        valorInventario: productos.reduce((suma, p) => suma + p.precio * p.stock, 0),
        porReponer: productos.filter(p => p.stock <= p.stockMinimo),
      };
    },

    formatearMoneda(valor) {
      return '$' + Number(valor).toLocaleString('es-CL');
    },

    formatearFecha(iso) {
      const fecha = new Date(iso);
      return fecha.toLocaleDateString('es-CL') + ' ' +
             fecha.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
    },
  };
})();
