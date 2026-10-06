# aqui importo los viewsets y filtros de django rest framework
from rest_framework import viewsets, filters
# aqui importo la vista generica y respuesta de drf
from rest_framework.views import APIView
from rest_framework.response import Response
# aqui importo los permisos para permitir consulta publica del catalogo externo
from rest_framework.permissions import AllowAny
# aqui importo el backend de django-filter para filtros estructurados
from django_filters.rest_framework import DjangoFilterBackend

# aqui importo los modelos del negocio
from .models import Categoria, Producto, MovimientoStock
# aqui importo los serializadores correspondientes
from .serializers import CategoriaSerializer, ProductoSerializer, MovimientoStockSerializer
# aqui importo el servicio de consulta a la api externa
from .servicios_api import consultar_catalogo_proveedor


# aqui defino el viewset de categorias con busqueda de texto
class CategoriaViewSet(viewsets.ModelViewSet):
    # aqui defino la consulta ordenada por nombre
    queryset = Categoria.objects.all().order_by('nombre')
    serializer_class = CategoriaSerializer
    # aqui configuro busqueda por nombre y descripcion
    search_fields = ['nombre', 'descripcion']
    filter_backends = [filters.SearchFilter]


# aqui defino el viewset de productos con relacion select_related y filtros avanzados
class ProductoViewSet(viewsets.ModelViewSet):
    # aqui optimizo la consulta sql usando select_related para traer la categoria de un solo viaje
    queryset = Producto.objects.select_related('categoria').all().order_by('-id')
    serializer_class = ProductoSerializer
    # aqui conecto los motores de filtrado busqueda y ordenamiento
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # aqui defino los campos exactos por los que el cliente puede filtrar
    filterset_fields = ['categoria', 'activo', 'unidad_medida']
    # aqui defino los campos de texto que el buscador evalua
    search_fields = ['nombre', 'sku']
    # aqui defino los campos habilitados para ordenar los resultados
    ordering_fields = ['precio', 'stock', 'fecha_registro', 'id']


# aqui defino el viewset de movimientos de stock con optimizacion de claves foraneas
class MovimientoStockViewSet(viewsets.ModelViewSet):
    # aqui cargo el producto y el usuario en una sola consulta sql
    queryset = MovimientoStock.objects.select_related('producto', 'registrado_por').all().order_by('-fecha')
    serializer_class = MovimientoStockSerializer
    # aqui configuro filtrado busqueda y orden para auditoria
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['producto', 'tipo']
    search_fields = ['observacion', 'producto__nombre', 'producto__sku']
    ordering_fields = ['fecha', 'cantidad', 'id']


# aqui defino el endpoint que expone la consulta al catalogo mayorista de la api externa
class CatalogoProveedorView(APIView):
    # aqui permito lectura abierta para el personal de abastecimiento
    permission_classes = [AllowAny]

    # aqui respondo la peticion get con los articulos encontrados en dummyjson
    def get(self, request):
        busqueda = request.query_params.get('q', None)
        categoria = request.query_params.get('categoria', None)
        limite_param = request.query_params.get('limite', '10')

        try:
            limite = int(limite_param)
        except ValueError:
            limite = 10

        # aqui ejecuto la llamada al servicio externo resiliente
        datos = consultar_catalogo_proveedor(busqueda=busqueda, categoria=categoria, limite=limite)
        return Response(datos)
