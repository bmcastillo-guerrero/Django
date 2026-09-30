# aqui importo los formularios base de django para construir los formularios de cuentas
from django import forms
# aqui importo el constructor de usuarios que aplica las reglas de contrasena seguras
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
# aqui importo el campo de nombre de usuario con su validacion de caracteres permitidos
from django.contrib.auth.forms import UsernameField
# aqui importo el modelo de usuario nativo de django
from django.contrib.auth.models import User
# aqui importo mi perfil para vincular el formulario de edicion de cuenta
from .models import PerfilUsuario


class FormularioIniciarSesion(AuthenticationForm):
    # aqui defino los campos que el usuario debe completar para entrar al sistema
    username = UsernameField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True,
            'placeholder': 'Tu nombre de usuario',
        })
    )
    # aqui defino el campo de contrasena con estilo bootstrap y sin exponer el texto
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña',
        }),
    )

    # aqui mejoro los mensajes de error para no filtrar información del sistema
    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos. Revisa tus datos e intenta de nuevo.',
        'inactive': 'Esta cuenta está desactivada. Contacta al administrador.',
    }


class FormularioRegistro(UserCreationForm):
    # aqui agrego el campo de correo electronico que no viene en el formulario original
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
        help_text='Solo se usará para avisos de stock, nunca se muestra públicamente.',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tucorreo@ejemplo.cl'}),
    )
    # aqui agrego un campo para el nombre real de la persona que usa el sistema
    nombre = forms.CharField(
        label='Nombre completo',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y apellido'}),
    )
    # aqui permito elegir el rol al registrarse pero el sistema siempre entregara el rol mas
    # bajo por seguridad y un administrador debe asignar el cambio desde el panel de django
    rol = forms.ChoiceField(
        label='Rol solicitado',
        choices=PerfilUsuario.ROLES,
        initial=PerfilUsuario.VENDEDOR,
        help_text='Por seguridad toda cuenta nueva nace como Vendedor. Un administrador puede elevar tu rol.',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        # aqui vinculo el formulario con el modelo de usuario de django
        model = User
        # aqui defino los campos que se veran en el formulario de alta
        fields = ('username', 'nombre', 'email', 'rol')
        # aqui defino las etiquetas legibles de los campos
        labels = {'username': 'Usuario'}

    # aqui valido que el correo no este repetido en otra cuenta
    def clean_email(self):
        # aqui obtengo el correo ya normalizado en minusculas por el propio formulario
        correo = self.cleaned_data['email']
        # aqui consulto si ya existe una cuenta registrada con ese correo
        if User.objects.filter(email__iexact=correo).exists():
            # aqui lanzo el error de validacion que se muestra bajo el campo
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo.')
        # aqui devuelvo el correo limpio para guardarlo en el modelo
        return correo

    # aqui ajusto el nombre completo separandolo en nombre y apellido de django
    def save(self, commit=True):
        # aqui llamo al guardado original del formulario nativo
        usuario = super().save(commit=False)
        # aqui separo el texto del nombre en la primera palabra y el resto
        partes = self.cleaned_data['nombre'].split()
        # aqui guardo la primera parte como first_name de django
        usuario.first_name = partes[0] if partes else ''
        # aqui guardo el resto de las palabras como last_name de django
        usuario.last_name = ' '.join(partes[1:]) if len(partes) > 1 else ''
        # aqui guardo el correo electronico en la cuenta
        usuario.email = self.cleaned_data['email']
        # aqui escribo en la base de datos solo si el formulario lo pide
        if commit:
            usuario.save()
        # aqui devuelvo la cuenta lista para iniciar sesion
        return usuario


class FormularioPerfil(forms.ModelForm):
    # aqui permito editar el nombre real y el correo de la cuenta del usuario
    first_name = forms.CharField(
        label='Nombre', max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Apellido', max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Correo electrónico', required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        # aqui vinculo el formulario con mi modelo de perfil
        model = PerfilUsuario
        # aqui solo permito editar el telefono porque el rol lo controla el administrador
        fields = ('telefono',)
        # aqui defino la etiqueta y el estilo del campo de telefono
        labels = {'telefono': 'Teléfono de contacto'}
        widgets = {
            'telefono': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 20, 'placeholder': '+56 9 0000 0000',
            }),
        }

    # aqui guardo los campos del usuario y el perfil con una sola operacion
    def save(self, commit=True):
        # aqui recupero la cuenta de django que esta asociada al formulario
        usuario = self.instance.usuario
        # aqui copio los datos del formulario al modelo de usuario nativo
        usuario.first_name = self.cleaned_data['first_name']
        usuario.last_name = self.cleaned_data['last_name']
        usuario.email = self.cleaned_data['email']
        # aqui delego el guardado del perfil sin escribirlo todavia en la base de datos
        perfil = super().save(commit=False)
        # aqui escribo en la base de datos solo cuando el formulario lo solicita
        if commit:
            # aqui guardo primero la cuenta porque el perfil depende de esa fila
            usuario.save()
            # aqui ahora si escribo el perfil ya con la cuenta actualizada
            perfil.save()
        # aqui devuelvo el perfil con los datos ya actualizados
        return perfil

    # aqui reviso que el correo no pertenezca a otra cuenta distinta de la actual
    def clean_email(self):
        # aqui obtengo el correo ya validado por el formulario
        correo = self.cleaned_data['email']
        # aqui busco otras cuentas que usen ese mismo correo
        otras = User.objects.filter(email__iexact=correo).exclude(pk=self.instance.usuario.pk)
        # aqui si existe otra cuenta lanzo el error de validacion
        if otras.exists():
            raise forms.ValidationError('Ese correo ya está en uso por otra cuenta.')
        # aqui devuelvo el correo para guardarlo
        return correo
