# aqui importo las señales de django para reaccionar a eventos del modelo de usuario
from django.contrib.auth.models import User
# aqui importo el modulo de señales de django
from django.db.models.signals import post_save
# aqui importo el emisor de señales para conectar mis funciones con los eventos
from django.dispatch import receiver
# aqui importo el logger del proyecto para auditar la creacion de cuentas
import logging

from .models import PerfilUsuario
from .roles import MAPA_ROL_GRUPO

# aqui creo el logger propio para dejar rastro de los accesos y altas de cuenta
logger = logging.getLogger('stockflow.cuentas')


@receiver(post_save, sender=User)
def crear_perfil_automatico(sender, instance, created, **kwargs):
    # aqui solo reacciono cuando la cuenta es nueva porque si ya existe solo se actualiza
    if not created:
        return
    # aqui creo el perfil asociado con un rol por defecto de vendedor
    perfil = PerfilUsuario.objects.create(usuario=instance, rol=PerfilUsuario.VENDEDOR)
    # aqui asigno el grupo de django que corresponde al rol por defecto
    grupo = MAPA_ROL_GRUPO.get(perfil.rol)
    # aqui busco el grupo en la base y se lo agrego al usuario si ya fue creado
    if grupo is not None:
        from django.contrib.auth.models import Group
        instancia_grupo = Group.objects.filter(name=grupo).first()
        if instancia_grupo is not None:
            instance.groups.add(instancia_grupo)
    # aqui dejo registrado en el archivo de logs que la cuenta fue creada
    logger.info('Cuenta creada: %s con perfil %s', instance.username, perfil.rol)
