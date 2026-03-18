# Script para reconfigurar los grupos medicos y tipos de cancer
# Run with: python manage.py reconfigurar_grupos_medicos

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from django.core.management.base import BaseCommand
from medicos.models import TipoCancer, MedicalGroup, DoctorGroupMembership


class Command(BaseCommand):
    help = 'Reconfigurar grupos medicos y tipos de cancer segun la nueva estructura'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('INICIANDO RECONFIGURACION DE GRUPOS MEDICOS'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        # 1. Guardar medicos del grupo de Tumores Pulmonares antes de eliminar
        self.stdout.write(self.style.NOTICE('\n[1] Guardando medicos del grupo de Tumores Pulmonares...'))
        medicos_tumores_pulmonares = []
        
        # Buscar el grupo de Tumores Pulmonares
        grupo_pulmonar = MedicalGroup.objects.filter(
            nombre__icontains='pulmonar'
        ).first()
        
        if grupo_pulmonar:
            membresias = DoctorGroupMembership.objects.filter(
                grupo=grupo_pulmonar,
                activo=True
            )
            medicos_tumores_pulmonares = [m.medico for m in membresias]
            self.stdout.write(self.style.SUCCESS(
                f'  Encontrados {len(medicos_tumores_pulmonares)} medicos en el grupo de Tumores Pulmonares'
            ))
            
            # Desactivar membresias antiguas
            membresias.update(activo=False)
            self.stdout.write(self.style.SUCCESS('  Membresias antiguas desactivadas'))
        else:
            self.stdout.write(self.style.WARNING('  No se encontro grupo de Tumores Pulmonares'))
        
        # 2. Eliminar todos los tipos de cancer existentes
        self.stdout.write(self.style.NOTICE('\n[2] Eliminando tipos de cancer existentes...'))
        tipos_eliminados = TipoCancer.objects.count()
        TipoCancer.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Eliminados {tipos_eliminados} tipos de cancer'))
        
        # 3. Eliminar todos los grupos medicos existentes
        self.stdout.write(self.style.NOTICE('\n[3] Eliminando grupos medicos existentes...'))
        grupos_eliminados = MedicalGroup.objects.count()
        MedicalGroup.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'  Eliminados {grupos_eliminados} grupos medicos'))
        
        # 4. Definir la nueva estructura de grupos y tipos de cancer
        self.stdout.write(self.style.NOTICE('\n[4] Creando nueva estructura de grupos medicos...'))
        
        grupos_data = [
            {
                'nombre': 'Consulta Multidisciplinaria de Vias Digestivas',
                'descripcion': 'Comite multidisciplinario especializado en tumores del aparato digestivo',
                'tipos_cancer': [
                    {'nombre': 'Esófago', 'codigo': 'ESOFAGO'},
                    {'nombre': 'Estomago', 'codigo': 'ESTOMAGO'},
                    {'nombre': 'Intestino Delgado', 'codigo': 'INTESTINO_DELGADO'},
                    {'nombre': 'Colon Recto', 'codigo': 'COLON_RECTO'},
                    {'nombre': 'Higado', 'codigo': 'HIGADO'},
                    {'nombre': 'Vias Biliares', 'codigo': 'VIAS_BILIARES'},
                    {'nombre': 'Pancreas', 'codigo': 'PANCREAS'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Tumores Toracico',
                'descripcion': 'Comite multidisciplinario especializado en tumores del torax',
                'tipos_cancer': [
                    {'nombre': 'Pulmon', 'codigo': 'PULMON'},
                    {'nombre': 'Pleura', 'codigo': 'PLEURA'},
                    {'nombre': 'Timoma', 'codigo': 'TIMOMA'},
                    {'nombre': 'Carcinoma Timico', 'codigo': 'CARCINOMA_TIMICO'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Mama',
                'descripcion': 'Comite multidisciplinario especializado en tumores de mama',
                'tipos_cancer': [
                    {'nombre': 'Mama', 'codigo': 'MAMA'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Cabeza y Cuello',
                'descripcion': 'Comite multidisciplinario especializado en tumores de cabeza y cuello',
                'tipos_cancer': [
                    {'nombre': 'Tumores de la boca', 'codigo': 'TUMOR_BOCA'},
                    {'nombre': 'Glandula Salivales', 'codigo': 'GLANDULA_SALIVAL'},
                    {'nombre': 'Laringe', 'codigo': 'LARINGE'},
                    {'nombre': 'Faringe', 'codigo': 'FARINGE'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Ginecologia',
                'descripcion': 'Comite multidisciplinario especializado en tumores ginecologicos',
                'tipos_cancer': [
                    {'nombre': 'Ovario', 'codigo': 'OVARIO'},
                    {'nombre': 'Cuello Uterino', 'codigo': 'CUELLO_UTERINO'},
                    {'nombre': 'Endometrio', 'codigo': 'ENDOMETRIO'},
                    {'nombre': 'Vulva', 'codigo': 'VULVA'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Linfoproliferativa',
                'descripcion': 'Comite multidisciplinario especializado en enfermedades linfoproliferativas',
                'tipos_cancer': [
                    {'nombre': 'Linfoma de Hodgkin', 'codigo': 'LINFOMA_HODGKIN'},
                    {'nombre': 'Linfoma No Hodgkin', 'codigo': 'LINFOMA_NO_HODGKIN'},
                    {'nombre': 'Mieloma Multiple', 'codigo': 'MIELOMA_MULTIPLE'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Urologia',
                'descripcion': 'Comite multidisciplinario especializado en tumores urologicos',
                'tipos_cancer': [
                    {'nombre': 'Prostata', 'codigo': 'PROSTATA'},
                    {'nombre': 'Rinon', 'codigo': 'RINON'},
                    {'nombre': 'Vias Urinarias y Vejiga', 'codigo': 'VIAS_URINARIAS_VEJIGA'},
                    {'nombre': 'Pene', 'codigo': 'PENE'},
                    {'nombre': 'Testiculo', 'codigo': 'TESTICULO'},
                ]
            },
            {
                'nombre': 'Consulta Multidisciplinaria de Tumores Perifericos',
                'descripcion': 'Comite multidisciplinario especializado en tumores oseos y de partes blandas',
                'tipos_cancer': [
                    {'nombre': 'Tumores Oseos', 'codigo': 'TUMOR_OSEOS'},
                    {'nombre': 'Tumores de Partes Blandas', 'codigo': 'TUMOR_PARTES_BLANDAS'},
                    {'nombre': 'Piel', 'codigo': 'PIEL'},
                ]
            },
        ]
        
        # 5. Crear los grupos y tipos de cancer
        grupos_creados = 0
        tipos_creados = 0
        
        for grupo_data in grupos_data:
            # Crear el grupo medico
            grupo, created = MedicalGroup.objects.get_or_create(
                nombre=grupo_data['nombre'],
                defaults={
                    'descripcion': grupo_data['descripcion'],
                    'activo': True
                }
            )
            
            if created:
                grupos_creados += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] Grupo creado: {grupo.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'  [!] Grupo ya existe: {grupo.nombre}'))
            
            # Crear los tipos de cancer y asociarlos al grupo
            for tc_data in grupo_data['tipos_cancer']:
                tc, tc_created = TipoCancer.objects.get_or_create(
                    codigo=tc_data['codigo'],
                    defaults={
                        'nombre': tc_data['nombre'],
                        'grupo_medico': grupo,
                        'activo': True
                    }
                )
                
                if tc_created:
                    tipos_creados += 1
                else:
                    # Actualizar la referencia al grupo
                    tc.grupo_medico = grupo
                    tc.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'    -> {len(grupo_data["tipos_cancer"])} tipos de cancer asociados'
            ))
        
        self.stdout.write(self.style.SUCCESS(f'\n  Total grupos creados: {grupos_creados}'))
        self.stdout.write(self.style.SUCCESS(f'  Total tipos de cancer creados/actualizados: {tipos_creados}'))
        
        # 6. Reasignar medicos de Tumores Pulmonares a Tumores Toracico
        self.stdout.write(self.style.NOTICE('\n[5] Reasignando medicos a Tumores Toracico...'))
        
        # Buscar el nuevo grupo de Tumores Toracico
        grupo_toracico = MedicalGroup.objects.filter(
            nombre__icontains='Tumores Toracico'
        ).first()
        
        if grupo_toracico and medicos_tumores_pulmonares:
            reasignados = 0
            for medico in medicos_tumores_pulmonares:
                # Crear nueva membresia en el grupo de Tumores Toracico
                membresia, created = DoctorGroupMembership.objects.get_or_create(
                    medico=medico,
                    grupo=grupo_toracico,
                    defaults={
                        'rol': 'miembro_regular',
                        'activo': True,
                        'disponible_asignacion_auto': True
                    }
                )
                if created:
                    reasignados += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'  [*] {reasignados} medicos reasignados al grupo de Tumores Toracico'
            ))
        elif not medicos_tumores_pulmonares:
            self.stdout.write(self.style.WARNING('  No habia medicos en el grupo de Tumores Pulmonares para reasignar'))
        else:
            self.stdout.write(self.style.ERROR('  [X] No se encontro el grupo de Tumores Toracico'))
        
        # 7. Resumen final
        self.stdout.write(self.style.WARNING('\n' + '=' * 70))
        self.stdout.write(self.style.WARNING('RESUMEN DE RECONFIGURACION'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'  * Grupos medicos eliminados: {grupos_eliminados}'))
        self.stdout.write(self.style.SUCCESS(f'  * Tipos de cancer eliminados: {tipos_eliminados}'))
        self.stdout.write(self.style.SUCCESS(f'  * Grupos medicos creados: {grupos_creados}'))
        self.stdout.write(self.style.SUCCESS(f'  * Tipos de cancer creados: {tipos_creados}'))
        
        # Mostrar estructura final
        self.stdout.write(self.style.WARNING('\nESTRUCTURA DE GRUPOS MEDICOS:'))
        for grupo in MedicalGroup.objects.all().order_by('nombre'):
            tipos = ', '.join([tc.nombre for tc in grupo.tipos_cancer.all()])
            self.stdout.write(f'  * {grupo.nombre}')
            self.stdout.write(f'    Tipos: {tipos}')
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Reconfiguracion completada exitosamente'))
