from django.core.management.base import BaseCommand
from cases.models import Case, MedicalOpinion, FinalReport

class Command(BaseCommand):
    help = 'Verificar información de un caso'
    
    def add_arguments(self, parser):
        parser.add_argument('case_id', type=str)
    
    def handle(self, *args, **options):
        case_id = options['case_id']
        
        caso = Case.objects.filter(case_id=case_id).first()
        if caso:
            self.stdout.write(f'Caso: {caso.case_id}')
            self.stdout.write(f'Estado: {caso.status}')
            self.stdout.write(f'Responsable: {caso.responsable}')
            self.stdout.write(f'Grupo médico: {caso.medical_group}')
            self.stdout.write('')
            
            # Buscar opiniones
            opiniones = MedicalOpinion.objects.filter(case=caso)
            self.stdout.write(f'Opiniones: {opiniones.count()}')
            for op in opiniones:
                self.stdout.write(f'  - Dr: {op.doctor}, Voto: {op.voto}, Comentario: {op.comentario_privado[:50] if op.comentario_privado else "Sin comentario"}...')
            self.stdout.write('')
            
            # Buscar informe final
            informe = FinalReport.objects.filter(case=caso).first()
            if informe:
                self.stdout.write(f'Informe final: {informe}')
                self.stdout.write(f'Conclusión: {informe.conclusion}')
                self.stdout.write(f'Justificación: {informe.justificacion[:100] if informe.justificacion else "Sin justificación"}...')
                self.stdout.write(f'PDF: {informe.pdf_file}')
            else:
                self.stdout.write('No hay informe final en la base de datos')
        else:
            self.stdout.write(self.style.ERROR(f'Caso {case_id} no encontrado'))
