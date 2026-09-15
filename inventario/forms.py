# aqui importo las herramientas de formularios de django
from django import forms

# aqui importo los modelos que se vincularan a los ModelForm
from .models import MovimientoStock, Producto


# aqui defino el formulario para crear y editar productos basado en el modelo Producto
class ProductoForm(forms.ModelForm):
    class Meta:
        # aqui vinculo el formulario al modelo Producto
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
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 20,
                'placeholder': 'SKU-0000-XX',
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# aqui defino el formulario para registrar movimientos de stock
class MovimientoForm(forms.ModelForm):
    class Meta:
        # aqui enlazo este formulario con el modelo MovimientoStock
        model = MovimientoStock
        # aqui indico los campos requeridos para la operacion
        fields = ['tipo', 'cantidad', 'observacion']
        # aqui defino las etiquetas visuales
        labels = {
            'tipo': 'Tipo',
            'cantidad': 'Cantidad',
            'observacion': 'Observación',
        }
        # aqui configuro los widgets con clases para mantener la estetica uniforme
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'observacion': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 200,
                'placeholder': 'Opcional',
            }),
        }

    # aqui implemento la validacion del lado del servidor para proteger la consistencia
    def clean(self):
        # aqui obtengo los datos limpios y procesados por django
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        # aqui rescato el producto vinculado que viene en los valores iniciales
        producto = self.initial.get('producto')

        # aqui compruebo que una salida no supere las unidades reales en existencia
        if producto and tipo == 'SALIDA' and cantidad:
            if cantidad > producto.stock:
                # aqui lanzo un error de validacion si la salida deja stock negativo
                raise forms.ValidationError(
                    f'Solo hay {producto.stock} unidades disponibles.'
                )
        # aqui retorno los datos validados
        return cleaned_data
