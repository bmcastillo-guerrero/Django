# aqui encapsulo la lectura de variables de entorno para mantener el settings limpio y seguro
import os
from pathlib import Path

# aqui defino los valores que se consideran verdade cuando llegan como texto desde el archivo .env
VERDADEROS = {'1', 'true', 't', 'yes', 'y', 'si', 'sí', 'on'}

# aqui defino los valores que se consideran falso cuando llegan como texto
FALSOS = {'0', 'false', 'f', 'no', 'n', 'off', ''}


def cargar_env(base_dir):
    # aqui defino la ruta del archivo .env que guarda la configuracion local sensible
    ruta_env = Path(base_dir) / '.env'
    # aqui salgo de la funcion si el archivo no existe porque es opcional en desarrollo
    if not ruta_env.exists():
        return
    # aqui abro el archivo en modo lectura recorriendo cada linea
    with ruta_env.open(encoding='utf-8') as archivo:
        for linea in archivo:
            # aqui descarto lineas vacias o que sean solo comentarios
            limpia = linea.strip()
            if not limpia or limpia.startswith('#') or '=' not in limpia:
                continue
            # aqui separo la clave del valor usando el primer igual como separador
            clave, _, valor = limpia.partition('=')
            # aqui elimino comillas envolventes que podrian quedar en el valor
            valor = valor.strip().strip('"').strip("'")
            # aqui defino la variable solo si todavia no existe en el sistema
            os.environ.setdefault(clave.strip(), valor)


def leer_texto(nombre, por_defecto=''):
    # aqui devuelvo el valor de la variable o el valor por defecto si no esta definida
    return os.environ.get(nombre, por_defecto)


def leer_booleano(nombre, por_defecto=False):
    # aqui obtengo el valor crudo de la variable de entorno
    crudo = os.environ.get(nombre)
    # aqui uso el valor por defecto cuando la variable no existe en absoluto
    if crudo is None:
        return por_defecto
    # aqui normalizo el texto a minusculas para comparar sin importar mayusculas
    normalizado = crudo.strip().lower()
    # aqui interpreto el texto usando las tablas de verdadero y falso definidas arriba
    if normalizado in VERDADEROS:
        return True
    if normalizado in FALSOS:
        return False
    # aqui devuelvo el valor por defecto si el texto no corresponde a ningun booleano conocido
    return por_defecto


def leer_entero(nombre, por_defecto=0):
    # aqui obtengo el valor crudo de la variable de entorno
    crudo = os.environ.get(nombre)
    # aqui uso el valor por defecto cuando la variable no existe
    if crudo is None or not crudo.strip():
        return por_defecto
    # aqui intento transformar el texto a numero entero
    try:
        return int(crudo.strip())
    except ValueError:
        # aqui ignoro silenciosamente los valores no numericos y devuelvo el valor por defecto
        return por_defecto


def leer_lista(nombre, por_defecto=''):
    # aqui parto del valor por defecto que tambien puede ser una lista ya separada
    if isinstance(por_defecto, (list, tuple)):
        elementos = list(por_defecto)
    else:
        elementos = por_defecto.split(',')
    # aqui reviso si existe una variable de entorno que reemplace al valor por defecto
    crudo = os.environ.get(nombre)
    # aqui uso la variable de entorno si fue definida en el archivo .env
    if crudo is not None:
        elementos = crudo.split(',')
    # aqui limpio cada elemento quitando espacios y los que quedaron vacios
    return [elemento.strip() for elemento in elementos if elemento.strip()]
