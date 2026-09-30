# aqui importo los tags de mensajes para asociarlos con clases de bootstrap
from django.contrib.messages import constants as messages
# aqui importo la excepcion propia de django para abortar el arranque con un mensaje claro
from django.core.exceptions import ImproperlyConfigured
# aqui importo mis lectoras de variables de entorno para sacar la configuracion sensible del codigo
from pathlib import Path

from .entorno import cargar_env, leer_booleano, leer_entero, leer_lista, leer_texto

# aqui defino la ruta base del proyecto usando pathlib
BASE_DIR = Path(__file__).resolve().parent.parent

# aqui cargo el archivo .env antes de leer cualquier variable de entorno
cargar_env(BASE_DIR)

# aqui leo la clave secreta desde el entorno para no dejarla escrita dentro del codigo
SECRET_KEY = leer_texto('DJANGO_SECRET_KEY')
# aqui defino el modo depuracion tambien desde el entorno para poder apagarlo en produccion
DEBUG = leer_booleano('DJANGO_DEBUG', True)


def obtener_clave_secreta():
    # aqui genero una clave aleatoria temporal para que el proyecto arranque en desarrollo
    import secrets
    return secrets.token_urlsafe(64)


# aqui valido que la clave secreta exista en produccion porque es obligatoria para firmar sesiones
if not SECRET_KEY:
    # aqui permito arrancar sin clave solo si estamos en modo depuracion
    if DEBUG:
        SECRET_KEY = obtener_clave_secreta()
    else:
        # aqui detengo el arranque indicando que falta definir la variable en el archivo .env
        raise ImproperlyConfigured(
            'Falta definir DJANGO_SECRET_KEY en el archivo .env para este entorno.'
        )

# aqui defino la lista de hosts permitidos para responder peticiones
ALLOWED_HOSTS = leer_lista('DJANGO_ALLOWED_HOSTS', ['127.0.0.1', 'localhost', 'testserver'])

# aqui defino los origenes protegidos por csrf utiles cuando la app se publica con https
CSRF_TRUSTED_ORIGINS = leer_lista('DJANGO_CSRF_TRUSTED_ORIGINS')

# aqui registro las aplicaciones instaladas tanto nativas como externas y del proyecto
INSTALLED_APPS = [
    # aqui cargo las aplicaciones base del framework django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # aqui cargo el filtro de numeros legibles para formatear precios en las plantillas
    'django.contrib.humanize',

    # aqui registro los paquetes externos de terceros
    'crispy_forms',
    'crispy_bootstrap5',

    # aqui registro la aplicacion de cuentas que maneja autenticacion sesiones y roles
    'cuentas.apps.CuentasConfig',
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
    # aqui agrego mi politica propia de expiracion de sesion por inactividad
    'cuentas.middleware.SesionInactivaMiddleware',
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
                # aqui agrego mi context processor que expone los datos de la sesion activa
                'cuentas.context_processors.sesion',
            ],
        },
    },
]

# aqui indico el punto de entrada para servidores compatibles con wsgi
WSGI_APPLICATION = 'stockflow.wsgi.application'

# aqui leo el motor de base de datos desde el entorno para poder cambiarlo sin tocar el codigo
MOTOR_BD = leer_texto('DJANGO_DB_ENGINE', 'django.db.backends.sqlite3')

# aqui detecto si el motor elegido es sqlite para usar una configuracion de un solo archivo
if MOTOR_BD.endswith('sqlite3'):
    DATABASES = {
        'default': {
            'ENGINE': MOTOR_BD,
            'NAME': BASE_DIR / leer_texto('DJANGO_DB_NAME', 'db.sqlite3'),
            # aqui aumento la espera para que sqlite no bloquee escrituras simultaneas
            'OPTIONS': {'timeout': 20},
            # aqui dejo la conexion sin persistencia porque sqlite abre el archivo en cada acceso
            'CONN_MAX_AGE': leer_entero('DJANGO_DB_CONN_MAX_AGE', 0),
        }
    }
else:
    # aqui dejo el bloque listo para PostgreSQL o MySQL tomando los datos de forma segura
    DATABASES = {
        'default': {
            'ENGINE': MOTOR_BD,
            'NAME': leer_texto('DJANGO_DB_NAME', 'stockflow'),
            'USER': leer_texto('DJANGO_DB_USER', 'stockflow'),
            'PASSWORD': leer_texto('DJANGO_DB_PASSWORD'),
            'HOST': leer_texto('DJANGO_DB_HOST', '127.0.0.1'),
            'PORT': leer_texto('DJANGO_DB_PORT', '5432'),
            # aqui mantengo viva la conexion para mejorar la persistencia y el rendimiento
            'CONN_MAX_AGE': leer_entero('DJANGO_DB_CONN_MAX_AGE', 60),
        }
    }

# aqui defino los validadores de contrasena para el sistema de cuentas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': leer_entero('DJANGO_PASSWORD_MIN_LENGTH', 8)},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# aqui configuro el tiempo maximo de vida de una sesion medida desde su creacion
SESSION_COOKIE_AGE = leer_entero('DJANGO_SESSION_COOKIE_AGE', 8 * 60 * 60)
# aqui indico el nombre propio de la cookie de sesion para no colisionar con otras apps del dominio
SESSION_COOKIE_NAME = leer_texto('DJANGO_SESSION_COOKIE_NAME', 'stockflow_sessionid')
# aqui la cookie nunca puede ser leida por javascript lo que reduce el riesgo de robo de sesion
SESSION_COOKIE_HTTPONLY = True
# aqui limito la cookie al mismo sitio para bloquear envios de sesion desde otros dominios
SESSION_COOKIE_SAMESITE = 'Lax'
# aqui guardo la sesion en la base de datos para poder revocarla desde el administrador
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# aqui cierro la sesion automaticamente cuando el usuario cierra el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# aqui evito refrescar la cookie en cada peticion para que la expiracion sea real y medible
SESSION_SAVE_EVERY_REQUEST = False

# aqui defino la vida maxima de la sesion medimos en minutos sin actividad antes de cerrarla
DJANGO_SESSION_INACTIVIDAD_MINUTOS = leer_entero('DJANGO_SESSION_INACTIVIDAD_MINUTOS', 30)

# aqui defino las rutas que usa django auth al iniciar y cerrar sesion
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# aqui establezco el idioma en espanol y la zona horaria de chile
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# aqui defino el prefijo de url para servir archivos estaticos
STATIC_URL = 'static/'
# aqui defino la carpeta donde django guardara los archivos estaticos compilados
STATIC_ROOT = BASE_DIR / 'staticfiles'

# aqui declaro la carpeta local static para que django cargue css iconos e imagenes
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# aqui prohibo que la aplicacion se muestre dentro de un iframe de otro sitio
X_FRAME_OPTIONS = 'DENY'
# aqui impide que el navegador adivine el tipo de contenido de las respuestas
SECURE_CONTENT_TYPE_NOSNIFF = True
# aqui limito la informacion que el navegador envia al visitar otro sitio
SECURE_REFERRER_POLICY = 'same-origin'
# aqui confio en el encabezado que envia el proxy para saber si la peticion original era https
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# aqui encripto las cookies de sesion y de proteccion csrf unicamente cuando hay https
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
# aqui fuerzo la redireccion a https para que ninguna petion viaje en texto plano
SECURE_SSL_REDIRECT = not DEBUG
# aqui mantengo activo el header de seguridad hsts durante un año en produccion
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# aqui creo la carpeta de registros para poder auditar los eventos del sistema
(BASE_DIR / 'registros').mkdir(exist_ok=True)

# aqui configuro el sistema de registros para tener trazas de seguridad y de negocio
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detallado': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'consola': {
            'class': 'logging.StreamHandler',
            'formatter': 'detallado',
        },
        # aqui uso un archivo rotativo para que los registros no crezcan sin limite
        'archivo_rotativo': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'registros' / 'stockflow.log',
            'maxBytes': 1024 * 1024,
            'backupCount': 3,
            'encoding': 'utf-8',
            'formatter': 'detallado',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['consola', 'archivo_rotativo'],
            'level': 'INFO',
            'propagate': False,
        },
        # aqui creo un logger propio para los eventos de negocio como movimientos y accesos
        'stockflow': {
            'handlers': ['consola', 'archivo_rotativo'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# aqui establezco el tipo de clave primaria automatica para los modelos
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# aqui defino el ancho maximo permitido para los archivos que se suben desde el formulario de perfil
DATA_UPLOAD_MAX_MEMORY_SIZE = leer_entero('DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE', 2 * 1024 * 1024)
# aqui limito el tamaño del cuerpo de cada peticion para frenar ataques de tipo fuerza bruta
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
