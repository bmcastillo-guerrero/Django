# aqui importo los formularios base de django para construir los formularios del catalogo
from django import forms
# aqui importo el widget de casillas multiples para editar categorias en bloque
from django.forms.models import inlineformset_factory

# aqui importo los modelos que se vinculan a los formularios del inventario
from .models import Categoria, MovimientoStock, Producto

# aqui defino el permiso que habilita a ver y editar los precios de venta
PERMISO_PRECIOS = 'inventario.puede_ver_precios'


# aqui defino el formulario de alta y edicion de categorias del catalogo
class CategoriaForm(forms.ModelForm):
    class Meta:
        # aqui vinculo el formulario al modelo de categoria
        model = Categoria
        # aqui indico los campos que se pueden gestionar
        fields = ['nombre', 'descripcion']
        # aqui defino las etiquetas legibles de cada campo
        labels = {'nombre': 'Nombre', 'descripcion': 'Descripción'}
        # aqui inyecto los estilos de bootstrap y los textos de ayuda
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 80,
                'placeholder': 'Ejemplo: Abarrotes',
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 200,
                'placeholder': 'Detalle opcional de la categoría',
            }),
        }

    # aqui valido que el nombre de la categoria no este repetido ignorando mayusculas
    def clean_nombre(self):
        # aqui obtengo el nombre ya limpiado de espacios por el formulario
        nombre = self.cleaned_data['nombre'].strip()
        # aqui consulto si existe otra categoria con ese mismo nombre en la base de datos
        repetidas = Categoria.objects.filter(nombre__iexact=nombre)
        # aqui excluyo el registro actual para que editar no se bloquee a si mismo
        if self.instance.pk:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        # aqui si el nombre ya existe lanzo el error de validacion bajo el campo
        if repetidas.exists():
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        # aqui devuelvo el nombre capitalizado para que la lista se vea ordenada
        return nombre.capitalize()


# aqui defino el formulario de alta y edicion de productos con validaciones rigurosas
class ProductoForm(forms.ModelForm):
    # aqui defino el constructor donde recibo el usuario para aplicar permisos de campo
    def __init__(self, *args, usuario=None, **kwargs):
        # aqui ejecuto el constructor original del formulario de django
        super().__init__(*args, **kwargs)
        # aqui guardo el usuario para saber que campos puede ver y editar
        self.usuario = usuario
        # aqui reviso si la cuenta tiene permiso para ver los precios de venta
        puede_precios = usuario is not None and usuario.has_perm(PERMISO_PRECIOS)
        # aqui si el usuario no tiene permiso de precios bloqueo el campo en solo lectura
        if not puede_precios:
            # aqui localizo el campo del precio dentro del formulario
            campo_precio = self.fields['precio']
            # aqui desactivo la validacion de obligatoriedad porque el valor viaja bloqueado
            campo_precio.required = False
            # aqui marco el campo como deshabilitado para que el navegador no lo envíe
            campo_precio.widget.attrs['disabled'] = True
            # aqui copio el precio actual o cero cuando es un producto nuevo
            campo_precio.initial = self.instance.precio or 0
            # aqui aviso en la ayuda que el precio lo controla la administracion
            campo_precio.help_text = 'Tu rol no puede modificar el precio. Lo define la administración.'

    class Meta:
        # aqui vinculo el formulario al modelo de producto
        model = Producto
        # aqui elijo la lista de campos que el usuario podra gestionar
        fields = [
            'nombre',
            'sku',
            'categoria',
            'precio',
            'stock',
            'stock_minimo',
            'unidad_medida',
            'activo',
        ]
        # aqui defino etiquetas legibles para cada campo en pantalla
        labels = {
            'nombre': 'Nombre',
            'sku': 'SKU',
            'categoria': 'Categoría',
            'precio': 'Precio ($)',
            'stock': 'Stock',
            'stock_minimo': 'Stock mínimo',
            'unidad_medida': 'Unidad de medida',
            'activo': 'Producto activo',
        }
        # aqui inyecto clases de bootstrap y atributos html a los widgets
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 120,
                'placeholder': 'Ejemplo: Arroz Grado 1',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control text-uppercase', 'maxlength': 20,
                'placeholder': 'ABE-1001-AB',
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # aqui normalizo el sku a mayusculas para que las busquedas sean consistentes
    def clean_sku(self):
        # aqui obtengo el sku enviado por el usuario
        sku = self.cleaned_data['sku'].strip()
        # aqui convierto todo el texto a mayusculas para unificar el formato
        sku = sku.upper()
        # aqui consulto si el sku ya pertenece a otro producto de la base de datos
        repetidos = Producto.objects.filter(sku=sku)
        # aqui excluyo el producto actual para que la edicion no se bloquee a si misma
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        # aqui si el sku esta tomado lanzo el error de validacion con mensaje explicito
        if repetidos.exists():
            raise forms.ValidationError(f'El SKU "{sku}" ya está registrado en otro producto.')
        # aqui devuelvo el sku normalizado en mayusculas
        return sku

    # aqui valido que el precio sea mayor que cero para evitar productos gratuitos por error
    def clean_precio(self):
        # aqui obtengo el precio ya convertido a decimal por el propio formulario
        precio = self.cleaned_data['precio']
        # aqui comparo el precio con cero para exigir un valor positivo
        if precio is not None and precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor que $0.')
        # aqui devuelvo el precio validado
        return precio

    # aqui valido que el stock minimo no sea mayor que el stock actual del producto
    def clean(self):
        # aqui parto de los datos ya validados por cada campo del formulario
        datos = super().clean()
        # aqui rescato el stock y el minimo para compararlos entre si
        stock = datos.get('stock')
        minimo = datos.get('stock_minimo')
        # aqui si ambos valores existen y el minimo supera al stock aviso del problema
        if stock is not None and minimo is not None and minimo > stock:
            # aqui agrego el error a la lista general del formulario para que se vea destacado
            self.add_error(
                'stock_minimo',
                'El stock mínimo no puede ser mayor que el stock actual '
                f'({stock} unidades disponibles).',
            )
        # aqui devuelvo los datos limpios para que el modelo se guarde
        return datos


# aqui defino el formulario que registra entradas y salidas de mercaderia
class MovimientoForm(forms.ModelForm):
    class Meta:
        # aqui enlazo este formulario con el modelo MovimientoStock
        model = MovimientoStock
        # aqui indico los campos requeridos para la operacion
        fields = ['tipo', 'cantidad', 'observacion']
        # aqui defino las etiquetas visuales
        labels = {
            'tipo': 'Tipo de movimiento',
            'cantidad': 'Cantidad',
            'observacion': 'Observación',
        }
        # aqui configuro los widgets con clases para mantener la estetica uniforme
        widgets = {
            'tipo': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'observacion': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 200,
                'placeholder': 'Opcional: motivo, proveedor o vendedor',
            }),
        }

    # aqui defino el constructor donde recibo el producto sobre el que se registra el movimiento
    def __init__(self, *args, producto=None, **kwargs):
        # aqui ejecuto el constructor original del formulario de modelo de django
        super().__init__(*args, **kwargs)
        # aqui guardo el producto en el formulario para usarlo en la validacion de stock
        self.producto = producto

    # aqui valido la operacion completa contra el stock real guardado en la base de datos
    def clean(self):
        # aqui parto de los datos ya validados por cada campo del formulario
        datos = super().clean()
        # aqui rescato el tipo de movimiento elegido por el usuario
        tipo = datos.get('tipo')
        # aqui rescato la cantidad pedida en el formulario
        cantidad = datos.get('cantidad')
        # aqui uso el producto entregado al constructor para validar contra su stock
        producto = self.producto
        # aqui si el producto no esta activo impido registrar cualquier movimiento
        if producto is not None and not producto.activo:
            # aqui lanzo el error que impide operar sobre productos descontinuados
            raise forms.ValidationError(
                f'El producto "{producto.nombre}" está descontinuado y no admite movimientos.'
            )
        # aqui si es una salida reviso que no se superen las unidades realmente disponibles
        if producto is not None and tipo == 'SALIDA' and cantidad:
            # aqui comparo la cantidad pedida contra el stock guardado en la base de datos
            if cantidad > producto.stock:
                raise forms.ValidationError(
                    f'Solo hay {producto.stock} unidades disponibles.'
                )
        # aqui devuelvo los datos ya validados
        return datos


# aqui defino el formulario de ajuste directo de stock reservado a bodegueros y administradores
class AjusteStockForm(forms.Form):
    # aqui defino el campo con el nuevo valor de stock que تريد dejar en el producto
    nuevo_stock = forms.IntegerField(
        label='Nuevo stock',
        min_value=0,
        max_value=1_000_000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        help_text='Este ajuste no genera movimiento en el historial.',
    )
    # aqui defino el campo opcional con la razon del ajuste manual
    motivo = forms.CharField(
        label='Motivo del ajuste',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'maxlength': 200,
            'placeholder': 'Ejemplo: corrección por conteo físico',
        }),
    )


# aqui defino el formulario de filtros del historial global de movimientos
class FiltroMovimientosForm(forms.Form):
    # aqui defino el buscador libre del historial
    query = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'maxlength': 80,
            'placeholder': 'SKU, producto o observación',
        }),
    )
    # aqui defino el filtro por tipo de movimiento
    tipo = forms.ChoiceField(
        label='Tipo',
        required=False,
        choices=[('', 'Todos los tipos')] + MovimientoStock.TIPOS,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


# aqui creo un formset para editar varios movimientos de un mismo producto a la vez
FormularioMovimientosProducto = inlineformset_factory(
    Producto,
    MovimientoStock,
    form=MovimientoForm,
    extra=1,
    can_delete=True,
)
