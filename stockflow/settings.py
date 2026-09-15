# aqui importo los tags de mensajes para asociarlos con clases de bootstrap
from django.contrib.messages import constants as messages
from pathlib import Path

# aqui defino la ruta base del proyecto usando pathlib
BASE_DIR = Path(__file__).resolve().parent.parent

# aqui configuro la clave secreta de la instalacion local
SECRET_KEY = 'django-insecure-x(q)kllg#g1z)igp-nhj&v6%-us6$99vaubq9@x3rgs8pswkef'

# aqui mantengo el modo depuracion activo durante el desarrollo
DEBUG = True

# aqui defino la lista de hosts permitidos para responder peticiones
ALLOWED_HOSTS = []

# aqui registro las aplicaciones instaladas tanto nativas como externas y del proyecto
INSTALLED_APPS = [
    # aqui cargo las aplicaciones base del framework django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # aqui registro los paquetes externos de terceros
    'crispy_forms',
    'crispy_bootstrap5',

    # aqui registro la aplicacion principal de inventario
    'inventario.apps.InventarioConfig',
]

# aqui configuro crispy forms para renderizar formularios con bootstrap 5
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# aqui vinculo los tipos de mensajes de django con clases de alerta de bootstrap
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# aqui configuro la cadena de middlewares para seguridad sesiones y peticiones
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# aqui indico el archivo principal de enrutamiento
ROOT_URLCONF = 'stockflow.urls'

# aqui configuro el motor de plantillas y la carpeta global templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # aqui enlazo la carpeta templates que esta en la raiz del proyecto
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# aqui indico el punto de entrada para servidores compatibles con wsgi
WSGI_APPLICATION = 'stockflow.wsgi.application'

# aqui configuro la base de datos relacional usando sqlite por defecto
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# aqui defino los validadores de contrasena para el sistema de cuentas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# aqui establezco el idioma en espanol y la zona horaria de chile
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# aqui defino el prefijo de url para servir archivos estaticos
STATIC_URL = 'static/'

# aqui declaro la carpeta local static para que django cargue css iconos e imagenes
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# aqui establezco el tipo de clave primaria automatica para los modelos
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
