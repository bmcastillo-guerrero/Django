from django import forms

from .models import MovimientoStock, Producto


class ProductoForm(forms.ModelForm):
    """Formulario de producto con widgets Bootstrap (mismo diseño del frontend)."""

    class Meta:
        model = Producto
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


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ['tipo', 'cantidad', 'observacion']
        labels = {
            'tipo': 'Tipo',
            'cantidad': 'Cantidad',
            'observacion': 'Observación',
        }
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'observacion': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 200,
                'placeholder': 'Opcional',
            }),
        }

    def clean(self):
        """Validación del lado del servidor: una salida no puede dejar stock negativo."""
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        producto = self.initial.get('producto')

        if producto and tipo == 'SALIDA' and cantidad:
            if cantidad > producto.stock:
                raise forms.ValidationError(
                    f'Solo hay {producto.stock} unidades disponibles.'
                )
        return cleaned_data
