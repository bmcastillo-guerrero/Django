"""
Comando para poblar la base de datos con datos de prueba.

Los datos fueron generados con apoyo de una herramienta de IA (recomendación
de librería Faker y diseño del set de datos), y luego validados y adaptados
al dominio del negocio (inventario de tienda).

Uso:  python manage.py seed_datos [--limpiar]
"""
import random

from django.core.management.base import BaseCommand
from faker import Faker

from inventario.models import Categoria, MovimientoStock, Producto


class Command(BaseCommand):
    help = 'Genera datos de prueba realistas usando Faker.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina los datos existentes antes de generar nuevos.',
        )

    def handle(self, *args, **options):
        fake = Faker(['es_ES'])

        if options['limpiar']:
            MovimientoStock.objects.all().delete()
            Producto.objects.all().delete()
            Categoria.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos anteriores eliminados.'))

        # Categorías base del rubro de una tienda de abarrotes / comercio general
        nombres_categorias = [
            ('Abarrotes', 'Productos alimenticios básicos'),
            ('Bebidas', 'Agua, jugos, gaseosas y otros líquidos'),
            ('Limpieza', 'Artículos de aseo del hogar'),
            ('Snacks', 'Colaciones y golosinas'),
            ('Cuidado personal', 'Higiene y cuidado personal'),
        ]
        categorias = []
        for nombre, descripcion in nombres_categorias:
            categoria, _ = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion},
            )
            categorias.append(categoria)

        productos_creados = 0
        for _ in range(20):
            categoria = random.choice(categorias)
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

            # Historial de movimientos coherente con el stock actual
            for _ in range(random.randint(1, 4)):
                tipo = random.choice(['ENTRADA', 'SALIDA'])
                MovimientoStock.objects.create(
                    producto=producto,
                    tipo=tipo,
                    cantidad=random.randint(1, 30),
                    observacion=fake.sentence(nb_words=6),
                )
            productos_creados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Datos generados: {len(categorias)} categorías y '
            f'{productos_creados} productos con movimientos.'
        ))
