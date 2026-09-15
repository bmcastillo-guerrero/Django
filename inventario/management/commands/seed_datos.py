# aqui importo random para seleccionar opciones aleatorias
import random

# aqui importo la clase base para crear comandos personalizados de django
from django.core.management.base import BaseCommand
# aqui importo faker como paquete externo para generar datos de prueba
from faker import Faker

# aqui importo los modelos del inventario que seran poblados
from inventario.models import Categoria, MovimientoStock, Producto


# aqui defino el comando personalizado seed_datos para la terminal
class Command(BaseCommand):
    # aqui defino el texto de ayuda que explica el comando
    help = 'Genera datos de prueba realistas usando Faker.'

    # aqui agrego el argumento opcional --limpiar para reiniciar la base de datos
    def add_arguments(self, parser):
        # aqui registro la bandera --limpiar
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina los datos existentes antes de generar nuevos.',
        )

    # aqui defino la logica principal que se ejecuta al llamar al comando
    def handle(self, *args, **options):
        # aqui inicializo faker en espanol para generar textos coherentes
        fake = Faker(['es_ES'])

        # aqui compruebo si el usuario paso la opcion --limpiar
        if options['limpiar']:
            # aqui borro los datos anteriores respetando la integridad referencial
            MovimientoStock.objects.all().delete()
            Producto.objects.all().delete()
            Categoria.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos anteriores eliminados.'))

        # aqui defino las categorias base de una tienda o minimarket
        nombres_categorias = [
            ('Abarrotes', 'Productos alimenticios basicos y no perecibles'),
            ('Bebidas', 'Agua, jugos, gaseosas y bebidas energeticas'),
            ('Limpieza', 'Articulos de aseo y desinfeccion del hogar'),
            ('Snacks', 'Galletas, frutos secos y golosinas'),
            ('Cuidado personal', 'Higiene personal, jabones y cuidado corporal'),
        ]
        categorias = []
        # aqui recorro la lista y creo o recupero cada categoria
        for nombre, descripcion in nombres_categorias:
            categoria, _ = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion},
            )
            categorias.append(categoria)

        productos_creados = 0
        # aqui itero para generar 20 productos variados con datos de faker
        for _ in range(20):
            # aqui selecciono una categoria al azar de las creadas
            categoria = random.choice(categorias)
            # aqui creo el producto asignando valores coherentes al rubro
            producto = Producto.objects.create(
                nombre=fake.word().capitalize() + ' ' + fake.word().capitalize(),
                sku=fake.unique.bothify(text='SKU-####-??').upper(),
                categoria=categoria,
                precio=round(random.uniform(500, 25000), 2),
                stock=random.randint(0, 120),
                stock_minimo=random.randint(5, 15),
                unidad_medida=random.choice(['UN', 'KG', 'LT', 'PAQ']),
                activo=random.random() > 0.1,
            )

            # aqui genero entre 1 y 4 movimientos para crear historial de bodega
            for _ in range(random.randint(1, 4)):
                tipo = random.choice(['ENTRADA', 'SALIDA'])
                MovimientoStock.objects.create(
                    producto=producto,
                    tipo=tipo,
                    cantidad=random.randint(1, 30),
                    observacion=fake.sentence(nb_words=6),
                )
            productos_creados += 1

        # aqui imprimo un mensaje de exito en la terminal con los resultados
        self.stdout.write(self.style.SUCCESS(
            f'Datos generados: {len(categorias)} categorias y '
            f'{productos_creados} productos con movimientos.'
        ))
