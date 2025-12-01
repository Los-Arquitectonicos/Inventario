"""
Management command para limpiar artículos de la base de datos.

Uso:
    # Eliminar TODOS los artículos (requiere confirmación)
    python manage.py limpiar_articulos --all
    
    # Eliminar artículos con más de X días
    python manage.py limpiar_articulos --dias 1
    
    # Modo dry-run (solo ver qué se eliminaría)
    python manage.py limpiar_articulos --all --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from inventario.models import Articulo
from datetime import datetime, timedelta
import sys


class Command(BaseCommand):
    help = 'Elimina artículos de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Eliminar TODOS los artículos (requiere confirmación)',
        )
        parser.add_argument(
            '--dias',
            type=int,
            help='Eliminar artículos con más de X días de antigüedad',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Modo simulación: solo muestra qué se eliminaría sin borrar',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Confirmar automáticamente (sin pedir confirmación)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_confirm = options['yes']
        
        # Determinar qué artículos eliminar
        if options['all']:
            articulos = Articulo.objects.all()
            mensaje = "TODOS los artículos"
        elif options['dias']:
            dias = options['dias']
            fecha_limite = datetime.now() - timedelta(days=dias)
            articulos = Articulo.objects.filter(fecha_ingreso__lt=fecha_limite)
            mensaje = f"artículos con más de {dias} día(s) de antigüedad"
        else:
            raise CommandError(
                'Debes especificar --all o --dias. '
                'Usa --help para ver las opciones.'
            )
        
        # Contar artículos
        total = articulos.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING(f'No hay artículos para eliminar.'))
            return
        
        # Mostrar información
        self.stdout.write('=' * 80)
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se eliminará nada'))
        else:
            self.stdout.write(self.style.ERROR('MODO ELIMINACIÓN REAL'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'\nSe {"eliminarían" if dry_run else "eliminarán"} {mensaje}:')
        self.stdout.write(f'Total de artículos: {total:,}')
        
        # Mostrar algunos ejemplos
        if total > 0:
            self.stdout.write('\nPrimeros 5 artículos:')
            for art in articulos[:5]:
                self.stdout.write(
                    f'  - ID: {art.id}, Código: {art.codigo_barras}, '
                    f'Fecha: {art.fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S")}'
                )
            if total > 5:
                self.stdout.write(f'  ... y {total - 5:,} más')
        
        self.stdout.write('')
        
        # Pedir confirmación
        if not dry_run and not auto_confirm:
            self.stdout.write(self.style.ERROR(
                f'\n ADVERTENCIA: Esta acción eliminará {total:,} artículos permanentemente.'
            ))
            confirmacion = input('\n¿Estás seguro? Escribe "SI" para continuar: ')
            
            if confirmacion != 'SI':
                self.stdout.write(self.style.WARNING('\nOperación cancelada.'))
                return
        
        # Ejecutar eliminación
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Dry-run completado. Se eliminarían {total:,} artículos.'
            ))
        else:
            self.stdout.write('\nEliminando artículos...')
            
            try:
                with transaction.atomic():
                    eliminados, detalles = articulos.delete()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'\n✓ Eliminación completada exitosamente.'
                    ))
                    self.stdout.write(f'Total eliminado: {eliminados:,} registros')
                    
                    # Mostrar detalles de cascada
                    if detalles:
                        self.stdout.write('\nDetalles de eliminación:')
                        for modelo, cantidad in detalles.items():
                            self.stdout.write(f'  - {modelo}: {cantidad:,}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'\n✗ Error durante la eliminación: {str(e)}'
                ))
                raise CommandError(f'Error al eliminar artículos: {str(e)}')
        
        self.stdout.write('=' * 80)
