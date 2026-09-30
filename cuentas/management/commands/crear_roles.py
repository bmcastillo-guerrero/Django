# aqui importo la clase base de los comandos personalizados de django
from django.core.management.base import BaseCommand
# aqui importo los grupos y permisos nativos de django para armar los roles del sistema
from django.contrib.auth.models import Group, Permission
# aqui importo el operador logico or del orm para filtrar permisos por pares exactos
from django.db.models import Q
# aqui importo el logger del proyecto para dejar traza de la creacion de roles
import logging

# aqui importo mi perfil y el mapa de permisos por rol que definí en roles.py
from cuentas.models import PerfilUsuario
from cuentas.roles import (
    GRUPO_ADMINISTRADORES,
    GRUPO_BODEGUEROS,
    GRUPO_VENDEDORES,
    MAPA_ROL_GRUPO,
    PERMISOS_POR_ROL,
)

# aqui creo el logger propio del comando
logger = logging.getLogger('stockflow.cuentas')


class Command(BaseCommand):
    # aqui escribo la ayuda que se ve al ejecutar el comando con la opcion help
    help = 'Crea los grupos de permisos de cada rol y las cuentas de demostración.'

    # aqui defino los argumentos que acepta el comando desde la terminal
    def add_arguments(self, parser):
        # aqui agrego la bandera para borrar las cuentas de demostracion antes de recrearlas
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina las cuentas de demostración antes de volver a crearlas.',
        )
        # aqui agrego la bandera para no crear las cuentas de demostracion
        parser.add_argument(
            '--sin-usuarios',
            action='store_true',
            help='Solo crea los grupos y permisos, sin generar cuentas de demostración.',
        )

    # aqui defino el metodo principal que ejecuta toda la logica del comando
    def handle(self, *args, **opciones):
        # aqui creo o actualizo los tres grupos con los permisos de cada rol
        self.crear_grupos()
        # aqui reviso si el usuario pidio borrar las cuentas de demostracion
        if opciones['limpiar']:
            # aqui elimino las cuentas creadas por este comando
            self.borrar_usuarios_demo()
        # aqui creo las cuentas de demostracion solo si el usuario no lo prohibio
        if not opciones['sin_usuarios']:
            # aqui genero una cuenta por cada rol con su clave de demostracion
            self.crear_usuarios_demo()
        # aqui confirmo en la terminal que el proceso termino correctamente
        self.stdout.write(self.style.SUCCESS('Roles de StockFlow listos.'))

    # aqui crea los grupos de django y les asigna los permisos de cada rol
    def crear_grupos(self):
        # aqui recorro cada rol definido en el mapa central de la aplicacion
        for rol, nombre_grupo in MAPA_ROL_GRUPO.items():
            # aqui obtengo el grupo creandolo si todavia no existe en la base de datos
            grupo, creado = Group.objects.get_or_create(name=nombre_grupo)
            # aqui consulto los objetos de permiso usando la lista de codigos completos
            codigos = PERMISOS_POR_ROL[rol]
            # aqui armo un filtro por pares exactos de app y codename con el operador logico or
            # si usara dos filtros independientes el orm devolveria tambien combinaciones ajenas
            consulta = Q(pk__in=[])
            for codigo in codigos:
                # aqui separo cada permiso escrito como app_label.codename
                app_label, _, nombre_permiso = codigo.partition('.')
                # aqui acumulo la condicion exacta de esa aplicacion y ese permiso
                consulta |= Q(content_type__app_label=app_label, codename=nombre_permiso)
            # aqui traduzco cada condicion al objeto Permission real de django
            permisos = Permission.objects.filter(consulta)
            # aqui reemplazo los permisos del grupo para que el rol quede siempre exacto
            grupo.permissions.set(permisos)
            # aqui aviso en la terminal cuanto permiso quedo asignado
            estado = 'creado' if creado else 'actualizado'
            self.stdout.write(f'  Grupo {nombre_grupo}: {estado} con {permisos.count()} permisos.')

    # aqui elimina las cuentas de demostracion creadas por este comando
    def borrar_usuarios_demo(self):
        # aqui borro las cuentas cuyos nombres terminan con el sufijo de demostracion
        from django.contrib.auth.models import User
        # aqui ejecuto el borrado de todas las cuentas de prueba de una sola vez
        borrados, _ = User.objects.filter(username__endswith='.demo').delete()
        # aqui informo en la terminal cuantas cuentas se eliminaron
        self.stdout.write(f'  Cuentas de demostración eliminadas: {borrados}.')

    # aqui crea una cuenta de demostracion por cada rol con permisos coherentes
    def crear_usuarios_demo(self):
        # aqui importo el modelo de usuario dentro del metodo para evitar ciclos de importacion
        from django.contrib.auth.models import User
        # aqui defino la clave compartida de las cuentas de demostracion
        clave_demo = 'Stockflow2026'
        # aqui defino la lista de cuentas con su rol correspondiente
        cuentas = [
            ('admin.demo', 'Ana', 'Administradora', PerfilUsuario.ADMINISTRADOR, True),
            ('bodega.demo', 'Beto', 'Bodeguero', PerfilUsuario.BODEGUERO, False),
            ('ventas.demo', 'Carla', 'Vendedora', PerfilUsuario.VENDEDOR, False),
        ]
        # aqui recorro cada cuenta definida en la lista anterior
        for usuario, nombre, apellido, rol, es_super in cuentas:
            # aqui si la cuenta ya existe la actualizo en vez de duplicarla
            cuenta, creado = User.objects.get_or_create(
                username=usuario,
                defaults={'email': f'{usuario}@ejemplo.cl'},
            )
            # aqui asigno nombre y apellido para que los listados se vean completos
            cuenta.first_name = nombre
            cuenta.last_name = apellido
            # aqui defino la clave de demostracion solo cuando la cuenta es nueva
            if creado:
                cuenta.set_password(clave_demo)
            # aqui guardo los cambios de la cuenta en la base de datos
            cuenta.save()
            # aqui actualizo el rol del perfil o lo creo si la cuenta es nueva
            perfil, _ = PerfilUsuario.objects.update_or_create(
                usuario=cuenta,
                defaults={'rol': rol},
            )
            # aqui limpio los grupos previos para dejar solo el grupo del rol actual
            cuenta.groups.clear()
            # aqui busco el grupo que corresponde al rol asignado
            grupo = Group.objects.filter(name=MAPA_ROL_GRUPO[rol]).first()
            # aqui agrego el grupo a la cuenta si el grupo existe
            if grupo is not None:
                cuenta.groups.add(grupo)
            # aqui marco como staff solo a la cuenta administradora para que entre al panel
            cuenta.is_staff = es_super
            # aqui defino como superusuario unicamente a la cuenta administradora
            cuenta.is_superuser = es_super
            # aqui guardo de nuevo los cambios de staff y permisos
            cuenta.save()
            # aqui registro la creacion de la cuenta en el archivo de logs
            logger.info('Cuenta de demostración %s creada con rol %s', usuario, perfil.rol)
            # aqui informo en la terminal el usuario y su clave de acceso
            self.stdout.write(f'  Usuario {usuario} · rol {perfil.get_rol_display()} · clave {clave_demo}')
