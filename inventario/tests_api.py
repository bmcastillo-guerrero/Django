# aqui importo el usuario nativo de django para pruebas de autenticacion
from django.contrib.auth.models import User
# aqui importo las herramientas de testeo de django rest framework
from rest_framework.test import APITestCase
from rest_framework import status
# aqui importo patch para aislar las llamadas de red externas durante los tests
from unittest.mock import patch

# aqui importo los modelos del inventario
from .models import Categoria, Producto, MovimientoStock


# aqui defino la suite de pruebas automatizadas para la api restful de stockflow
class StockFlowAPITests(APITestCase):

    # aqui configuro el entorno inicial y los datos de prueba
    def setUp(self):
        # aqui creo el usuario para validar la emision y uso de tokens jwt
        self.user = User.objects.create_user(
            username='estudiante_test',
            password='PasswordSeguro123!'
        )

        # aqui creo la categoria de prueba
        self.categoria = Categoria.objects.create(
            nombre='Abarrotes y Alimentos',
            descripcion='Artículos básicos de consumo y despensa'
        )

        # aqui creo el producto inicial de prueba con sku valido
        self.producto = Producto.objects.create(
            nombre='Arroz Grado 1 1kg',
            sku='ARZ-1001-CL',
            categoria=self.categoria,
            precio=1490.00,
            stock=50,
            stock_minimo=10,
            unidad_medida='UN',
            activo=True
        )

    # 1. verifica lectura publica del catalogo en json paginado (GET 200 OK)
    def test_listado_productos_publico(self):
        # aqui consulto el endpoint sin enviar cabecera de autenticacion
        response = self.client.get('/api/v1/productos/')
        # aqui compruebo codigo 200 ok
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # aqui verifico que la respuesta incluya paginacion y lista de resultados
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    # 2. verifica detalle de producto y campos calculados de negocio (GET 200 OK)
    def test_detalle_producto_y_propiedades_calculadas(self):
        # aqui consulto el detalle del producto por su clave primaria
        response = self.client.get(f'/api/v1/productos/{self.producto.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # aqui verifico campos calculados que enriquecen el json sin recargar la base de datos
        self.assertEqual(response.data['categoria_nombre'], 'Abarrotes y Alimentos')
        self.assertEqual(float(response.data['valor_inventario']), 74500.0)
        self.assertFalse(response.data['necesita_reposicion'])

    # 3. verifica blindaje de seguridad: rechazo de creacion sin credenciales (POST 401 Unauthorized)
    def test_creacion_sin_token_rechazada(self):
        # aqui preparo un payload para intentar crear sin token
        payload = {
            'nombre': 'Producto No Autorizado',
            'sku': 'NOA-0001-XX',
            'categoria': self.categoria.id,
            'precio': 5000,
            'stock': 10,
            'stock_minimo': 2
        }
        response = self.client.post('/api/v1/productos/', payload, format='json')
        # aqui compruebo que el servidor rechaza la peticion anonima con 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 4. verifica emision de jwt y creacion exitosa de producto (POST 201 Created)
    def test_creacion_con_token_jwt(self):
        # aqui solicito el par de tokens enviando credenciales al endpoint de login
        login_res = self.client.post('/api/token/', {
            'username': 'estudiante_test',
            'password': 'PasswordSeguro123!'
        }, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_res.data)
        self.assertIn('refresh', login_res.data)
        token_acceso = login_res.data['access']

        # aqui adjunto la cabecera bearer requerida para mutaciones
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_acceso}')

        nuevo_payload = {
            'nombre': 'Aceite Vegetal 900ml',
            'sku': 'ACE-2002-CL',
            'categoria': self.categoria.id,
            'precio': 2190.00,
            'stock': 30,
            'stock_minimo': 5,
            'unidad_medida': 'UN'
        }
        # aqui envio la peticion post con el producto nuevo
        response = self.client.post('/api/v1/productos/', nuevo_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sku'], 'ACE-2002-CL')
        # aqui confirmo persistencia real en la base de datos
        self.assertTrue(Producto.objects.filter(sku='ACE-2002-CL').exists())

    # 5. verifica validacion de negocio en el serializador (precio negativo -> 400 Bad Request)
    def test_validacion_precio_negativo(self):
        # aqui autentico con token jwt
        login_res = self.client.post('/api/token/', {
            'username': 'estudiante_test',
            'password': 'PasswordSeguro123!'
        }, format='json')
        token_acceso = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_acceso}')

        payload_invalido = {
            'nombre': 'Producto con Precio Inválido',
            'sku': 'ERR-9999-CL',
            'categoria': self.categoria.id,
            'precio': -1500,  # aqui pruebo un valor prohibido por la regla
            'stock': 10,
            'stock_minimo': 2
        }
        response = self.client.post('/api/v1/productos/', payload_invalido, format='json')
        # aqui compruebo que devuelve 400 y detalla el campo erroneo
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('precio', response.data)

    # 6. verifica validacion de movimientos: rechazo de salidas superiores al stock fisico
    def test_validacion_salida_mayor_a_stock(self):
        # aqui autentico con token jwt
        login_res = self.client.post('/api/token/', {
            'username': 'estudiante_test',
            'password': 'PasswordSeguro123!'
        }, format='json')
        token_acceso = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_acceso}')

        # aqui intento retirar 200 unidades cuando el stock es solo 50
        payload_movimiento_excesivo = {
            'producto': self.producto.id,
            'tipo': 'SALIDA',
            'cantidad': 200,
            'observacion': 'Intento de venta sin existencias físicas'
        }
        response = self.client.post('/api/v1/movimientos/', payload_movimiento_excesivo, format='json')
        # aqui compruebo que la capa de validacion bloquea la operacion
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 7. verifica respuesta consistente en json ante recurso inexistente (GET 404 Not Found)
    def test_recurso_inexistente_retorna_404_json(self):
        response = self.client.get('/api/v1/productos/999999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # aqui verifico que devuelva json estructurado con la clave detail
        self.assertIn('detail', response.data)

    # 8. verifica endpoint de integracion externa con dummyjson usando mock para aislamiento
    @patch('inventario.api_views.consultar_catalogo_proveedor')
    def test_endpoint_proveedores_externos(self, mock_proveedor):
        # aqui simulo la respuesta del servicio externo para no depender de la latencia de internet
        mock_proveedor.return_value = {
            'disponible': True,
            'total': 1,
            'proveedor': 'DummyJSON Wholesale Market',
            'productos': [
                {
                    'id_externo': 1,
                    'titulo': 'Essence Mascara Lash Princess',
                    'categoria_proveedor': 'beauty',
                    'precio_usd': 9.99,
                    'stock_proveedor': 99,
                    'marca': 'Essence',
                    'sku_externo': 'BEA-1001-PR',
                    'calificacion': 4.94,
                    'disponibilidad': 'In Stock',
                    'minimo_pedido': 5
                }
            ]
        }

        # aqui consulto el endpoint proxy de proveedores
        response = self.client.get('/api/v1/proveedores/?q=mascara')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # aqui compruebo los atributos entregados
        self.assertTrue(response.data['disponible'])
        self.assertEqual(response.data['proveedor'], 'DummyJSON Wholesale Market')
        self.assertEqual(len(response.data['productos']), 1)
