# aqui importo json y urllib para consultar servicios web externos sin dependencias pesadas
import json
import urllib.parse
import urllib.request


# aqui defino el servicio que consulta el catalogo de proveedores mayoristas en dummyjson
def consultar_catalogo_proveedor(busqueda=None, categoria=None, limite=10):
    """
    aqui consulto la api externa de https://dummyjson.com/products
    para traer articulos de proveedores de referencia de mercado y abastecimiento.
    """
    url_base = "https://dummyjson.com/products"

    # aqui determino si la consulta es por busqueda por categoria o listado general
    if busqueda:
        parametro = urllib.parse.quote(busqueda)
        url = f"{url_base}/search?q={parametro}&limit={limite}"
    elif categoria:
        parametro = urllib.parse.quote(categoria)
        url = f"{url_base}/category/{parametro}?limit={limite}"
    else:
        url = f"{url_base}?limit={limite}"

    try:
        # aqui configuro la peticion http con cabecera de agente y tiempo de espera de 3 segundos
        peticion = urllib.request.Request(
            url,
            headers={'User-Agent': 'StockFlowBodega/1.0 (Sistema de Inventario)'}
        )
        with urllib.request.urlopen(peticion, timeout=3) as respuesta:
            if respuesta.status == 200:
                cuerpo = respuesta.read().decode('utf-8')
                datos = json.loads(cuerpo)
                productos_externos = []

                # aqui transformo cada articulo del proveedor al formato de analisis de bodega
                for item in datos.get('products', []):
                    productos_externos.append({
                        'id_externo': item.get('id'),
                        'titulo': item.get('title'),
                        'categoria_proveedor': item.get('category'),
                        'precio_usd': float(item.get('price', 0)),
                        'stock_proveedor': item.get('stock', 0),
                        'marca': item.get('brand', 'Genérico'),
                        'sku_externo': item.get('sku', f"EXT-{item.get('id')}"),
                        'calificacion': item.get('rating', 0),
                        'disponibilidad': item.get('availabilityStatus', 'Disponible'),
                        'minimo_pedido': item.get('minimumOrderQuantity', 1),
                    })

                # aqui entrego la respuesta estructurada y lista para consumo
                return {
                    'disponible': True,
                    'total': datos.get('total', len(productos_externos)),
                    'proveedor': 'DummyJSON Wholesale Market',
                    'productos': productos_externos,
                }
    except Exception as error:
        # aqui capturo cualquier falla de red o tiempo de espera para que la app siga funcionando
        return {
            'disponible': False,
            'proveedor': 'DummyJSON Wholesale Market',
            'error': str(error),
            'productos': [],
        }

    return {'disponible': False, 'productos': []}
