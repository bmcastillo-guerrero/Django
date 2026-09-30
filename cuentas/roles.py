# aqui importo el modelo de perfil para saber los nombres exactos de cada rol
from .models import PerfilUsuario

# aqui defino el nombre del grupo con control total sobre el sistema
GRUPO_ADMINISTRADORES = 'Administradores'
# aqui defino el nombre del grupo encargado de la bodega y los movimientos
GRUPO_BODEGUEROS = 'Bodegueros'
# aqui defino el nombre del grupo que solo consulta el catalogo
GRUPO_VENDEDORES = 'Vendedores'

# aqui relaciono cada rol de mi perfil con el grupo de django que lo representa
MAPA_ROL_GRUPO = {
    PerfilUsuario.ADMINISTRADOR: GRUPO_ADMINISTRADORES,
    PerfilUsuario.BODEGUERO: GRUPO_BODEGUEROS,
    PerfilUsuario.VENDEDOR: GRUPO_VENDEDORES,
}

# aqui defino los permisos del modelo inventario que puede usar cada tipo de usuario
# cada permiso se declara como el par app_label y codename separado por una coma
PERMISOS_POR_ROL = {
    PerfilUsuario.ADMINISTRADOR: [
        'inventario.add_producto', 'inventario.change_producto',
        'inventario.delete_producto', 'inventario.view_producto',
        'inventario.puede_ver_precios', 'inventario.puede_ajustar_stock',
        'inventario.puede_reasignar_categorias',
        'inventario.add_categoria', 'inventario.change_categoria',
        'inventario.delete_categoria', 'inventario.view_categoria',
        'inventario.add_movimientostock', 'inventario.change_movimientostock',
        'inventario.delete_movimientostock', 'inventario.view_movimientostock',
        'inventario.puede_anular_movimiento',
        'cuentas.puede_asignar_roles', 'cuentas.puede_ver_cuentas',
    ],
    PerfilUsuario.BODEGUERO: [
        'inventario.view_producto', 'inventario.add_producto',
        'inventario.change_producto', 'inventario.view_categoria',
        'inventario.add_categoria', 'inventario.change_categoria',
        'inventario.add_movimientostock', 'inventario.view_movimientostock',
        'inventario.puede_ver_precios', 'inventario.puede_ajustar_stock',
    ],
    PerfilUsuario.VENDEDOR: [
        'inventario.view_producto', 'inventario.view_categoria',
    ],
}
