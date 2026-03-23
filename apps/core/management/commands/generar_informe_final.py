"""
Comando de Django para generar el informe final (PDF) de un caso.
"""
from django.core.management.base import BaseCommand, CommandError
from cases.models import Case, FinalReport, MedicalOpinion
from django.core.files.base import ContentFile
from django.conf import settings
import io
import logging

logger = logging.getLogger(__name__)

# Importar reportlab solo si está disponible
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab no está instalado. El PDF no se generará.")


class Command(BaseCommand):
    help = 'Genera el informe final (PDF) para un caso específico'
    
    def add_arguments(self, parser):
        parser.add_argument('case_id', type=str, help='ID del caso (ej: CASO-226F2822940C)')
        parser.add_argument('--force', action='store_true', help='Sobrescribir el informe existente')
    
    def handle(self, *args, **options):
        if not REPORTLAB_AVAILABLE:
            raise CommandError("reportlab no está instalado. Instala pip install reportlab")
        
        case_id = options['case_id']
        force = options.get('force', False)
        
        # Buscar el caso
        try:
            caso = Case.objects.get(case_id=case_id)
        except Case.DoesNotExist:
            raise CommandError(f"Case with ID {case_id} does not exist")
        
        # Verificar si ya existe el informe final
        informe_existente = FinalReport.objects.filter(case=caso).first()
        if informe_existente and not force:
            self.stdout.write(self.style.WARNING(f"El caso {case_id} ya tiene un informe final. Usa --force para sobrescribir."))
            return
        
        # Obtener las opiniones médicas
        opiniones = MedicalOpinion.objects.filter(case=caso).select_related('doctor', 'doctor__usuario')
        
        if not opiniones.exists():
            raise CommandError(f"El caso {case_id} no tiene opiniones médicas")
        
        # Determinar conformidad basada en los votos
        votos_acuerdo = opiniones.filter(voto='acuerdo').count()
        votos_desacuerdo = opiniones.filter(voto='desacuerdo').count()
        votos_abstencion = opiniones.filter(voto='abstencion').count()
        
        if votos_acuerdo > votos_desacuerdo:
            conformidad = 'acuerdo'
            explicacion = 'La mayoría de los especialistas están de acuerdo con el tratamiento propuesto.'
        elif votos_desacuerdo > votos_acuerdo:
            conformidad = 'desacuerdo'
            explicacion = 'La mayoría de los especialistas no están de acuerdo con el tratamiento propuesto.'
        else:
            conformidad = 'consenso_parcial'
            explicacion = 'No hay consenso claro entre los especialistas.'
        
        # Obtener el responsable
        responsable = caso.responsable
        
        # Crear o actualizar el informe final
        informe_final, created = FinalReport.objects.get_or_create(
            case=caso,
            defaults={
                'conclusion': conformidad,
                'justificacion': explicacion,
                'recomendaciones': 'Generado automáticamente',
                'redactado_por': responsable
            }
        )
        
        if not created and force:
            informe_final.conclusion = conformidad
            informe_final.justificacion = explicacion
            informe_final.recomendaciones = 'Generado automáticamente'
            if responsable:
                informe_final.redactado_por = responsable
            informe_final.save()
        
        # Generar el PDF
        pdf_filename = f'respuesta_{caso.case_id}.pdf'
        buffer = io.BytesIO()
        
        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            story.append(Paragraph("SEGUNDA OPINIÓN MÉDICA", styles['Title']))
            story.append(Spacer(1, 0.2*inch))
            
            # Información del caso
            story.append(Paragraph("INFORMACIÓN DEL CASO", styles['Heading2']))
            info_data = [
                ["ID del Caso:", caso.case_id],
                ["Fecha de Solicitud:", caso.created_at.strftime('%d/%m/%Y') if caso.created_at else ''],
                ["Tipo de Cáncer:", str(caso.tipo_cancer) if caso.tipo_cancer else 'No especificado'],
                ["Diagnóstico:", caso.primary_diagnosis or 'No especificado'],
                ["Estadio:", caso.estadio or 'No especificado'],
            ]
            
            t = Table(info_data, colWidths=[2*inch, 4*inch])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3*inch))
            
            # Votación
            story.append(Paragraph("RESULTADO DE LA VOTACIÓN", styles['Heading2']))
            story.append(Paragraph(f"Votos a favor: {votos_acuerdo}", styles['Normal']))
            story.append(Paragraph(f"Votos en contra: {votos_desacuerdo}", styles['Normal']))
            story.append(Paragraph(f"Abstenciones: {votos_abstencion}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Opiniones de los especialistas
            story.append(Paragraph("OPINIONES DE LOS ESPECIALISTAS", styles['Heading2']))
            for opinion in opiniones:
                voto_display = opinion.get_voto_display()
                story.append(Paragraph(f"<b>Dr. {opinion.doctor.nombre_completo}</b>: {voto_display}", styles['Normal']))
                if opinion.comentario_privado:
                    story.append(Paragraph(f"  Comentario: {opinion.comentario_privado}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.3*inch))
            
            # Conclusión
            story.append(Paragraph("CONCLUSIÓN", styles['Heading2']))
            story.append(Paragraph(explicacion, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Recomendaciones
            story.append(Paragraph("RECOMENDACIONES", styles['Heading2']))
            story.append(Paragraph("Se recomienda continuar con el seguimiento regular y consultar con el oncólogo tratante para definir el plan de tratamiento más adecuado según el caso específico.", styles['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            
            # Guardar el PDF
            if informe_final.pdf_file:
                informe_final.pdf_file.delete()
            informe_final.pdf_file.save(pdf_filename, ContentFile(buffer.getvalue()))
            informe_final.save()
            
            self.stdout.write(self.style.SUCCESS(f"PDF generado correctamente para el caso {case_id}"))
            self.stdout.write(f"Ubicación: {informe_final.pdf_file.path}")
            
        except Exception as e:
            logger.exception(f"Error generando PDF para caso {case_id}")
            raise CommandError(f"Error generando PDF: {str(e)}")
