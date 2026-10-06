# aqui importo las herramientas de serializacion de django rest framework
from rest_framework import serializers
# aqui importo los modelos del inventario
from .models import Categoria, Producto, MovimientoStock
# aqui importo el servicio de negocio para registrar movimientos de stock atomicos
from .servicios import registrar_movimiento
from .excepciones import StockInsuficienteError, ProductoInactivoError, MovimientoInvalidoError


# aqui defino el serializador de categoria para convertir el modelo a json
class CategoriaSerializer(serializers.ModelSerializer):
    # aqui expongo la propiedad calculada del total de productos asociados
    total_productos = serializers.ReadOnlyField()

    class Meta:
        # aqui enlazo el modelo categoria
        model = Categoria
        # aqui defino la lista explicita de campos sin usar all para prevenir exposicion accidental
        fields = ['id', 'nombre', 'descripcion', 'total_productos']


# aqui defino el serializador de producto con validaciones de negocio en el servidor
class ProductoSerializer(serializers.ModelSerializer):
    # aqui agrego campos calculados de solo lectura que enriquecen el json sin sobrecargar la bd
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    necesita_reposicion = serializers.ReadOnlyField()
    valor_inventario = serializers.ReadOnlyField()
    porcentaje_stock = serializers.ReadOnlyField()

    class Meta:
        # aqui vinculo el modelo producto
        model = Producto
        # aqui defino la lista exacta de campos expuestos al cliente
        fields = [
            'id',
            'nombre',
            'sku',
            'categoria',
            'categoria_nombre',
            'precio',
            'stock',
            'stock_minimo',
            'unidad_medida',
            'activo',
            'necesita_reposicion',
            'valor_inventario',
            'porcentaje_stock',
            'fecha_registro',
            'actualizado_en',
        ]
        # aqui protejo las marcas de tiempo para que sean asignadas solo por el servidor
        read_only_fields = ['fecha_registro', 'actualizado_en']

    # aqui valido en el servidor que el precio unitario no sea un numero negativo
    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio del producto no puede ser un valor negativo.")
        return value

    # aqui valido que las existencias iniciales no sean negativas
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser un número negativo.")
        return value

    # aqui valido que el umbral minimo de reposicion sea mayor o igual a cero
    def validate_stock_minimo(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock mínimo no puede ser negativo.")
        return value

    # aqui normalizo el sku para asegurar formato en mayusculas y sin espacios en blanco
    def validate_sku(self, value):
        sku_limpio = value.strip().upper()
        return sku_limpio


# aqui defino el serializador para registrar y auditar movimientos de mercaderia
class MovimientoStockSerializer(serializers.ModelSerializer):
    # aqui expongo datos legibles del producto para que el cliente no requiera consultas extras
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_sku = serializers.ReadOnlyField(source='producto.sku')
    valor_movimiento = serializers.ReadOnlyField()

    class Meta:
        # aqui vinculo el modelo de movimiento de stock
        model = MovimientoStock
        # aqui declaro los campos del movimiento
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'producto_sku',
            'tipo',
            'cantidad',
            'observacion',
            'fecha',
            'valor_movimiento',
        ]
        # aqui marco la fecha de registro como solo lectura
        read_only_fields = ['fecha']

    # aqui valido que la cantidad a mover sea un entero mayor o igual a 1
    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad del movimiento debe ser al menos 1 unidad.")
        return value

    # aqui aplico la validacion cruzada de negocio antes de tocar la base de datos
    def validate(self, attrs):
        producto = attrs.get('producto')
        tipo = attrs.get('tipo')
        cantidad = attrs.get('cantidad')

        # aqui verifico que no se solicite una salida mayor a las existencias reales
        if tipo == 'SALIDA' and producto and cantidad:
            if cantidad > producto.stock:
                raise serializers.ValidationError({
                    'cantidad': f"Stock insuficiente en bodega. Stock actual: {producto.stock}, retiro solicitado: {cantidad}."
                })
        return attrs

    # aqui conecto la creacion con la capa de servicios transaccional
    def create(self, validated_data):
        # aqui obtengo el usuario autenticado que viene en la peticion http
        request = self.context.get('request')
        usuario = request.user if request and request.user.is_authenticated else None

        try:
            # aqui ejecuto el registro mediante el servicio atomico para actualizar el stock fisico
            return registrar_movimiento(
                producto=validated_data['producto'],
                tipo=validated_data['tipo'],
                cantidad=validated_data['cantidad'],
                observacion=validated_data.get('observacion', ''),
                usuario=usuario,
            )
        except (StockInsuficienteError, ProductoInactivoError, MovimientoInvalidoError) as error:
            # aqui transformo la excepcion de negocio en un error estructurado de serializacion
            raise serializers.ValidationError({'detail': str(error)})
