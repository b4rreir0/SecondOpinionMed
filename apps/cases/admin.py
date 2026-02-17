from django.contrib import admin
from .models import Case, CaseDocument, SecondOpinion, CaseAuditLog, MedicalOpinion, FinalReport
from .mdt_models import (
    MDTMessage, MDTMessageAttachment, UserPresence, AlgoritmoConfig,
    AsignacionAuditLog, ConsensusWorkflow, ConsensusVersion, ConsensusVote,
    OpinionDisidente, ClinicalTemplate, AnatomicalRegion, UserPreferences
)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """Admin para el modelo Case"""
    
    list_display = ('case_id', 'primary_diagnosis', 'patient_name', 'doctor_name', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'specialty_required')
    search_fields = ('case_id', 'patient__email', 'doctor__email', 'primary_diagnosis')
    readonly_fields = ('case_id', 'created_at', 'updated_at', 'assigned_at', 'completed_at')
    
    def patient_name(self, obj):
        return obj.patient.email
    patient_name.short_description = 'Paciente'
    
    def doctor_name(self, obj):
        return obj.doctor.email if obj.doctor else 'No asignado'
    doctor_name.short_description = 'Médico'
    
    fieldsets = (
        ('Identificación', {'fields': ('case_id',)}),
        ('Participantes', {'fields': ('patient', 'doctor')}),
        ('Información del Caso', {'fields': ('primary_diagnosis', 'specialty_required', 'description')}),
        ('Estado', {'fields': ('status',)}),
        ('Auditoría', {'fields': ('created_at', 'updated_at', 'assigned_at', 'completed_at')}),
    )


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    """Admin para el modelo CaseDocument"""
    
    list_display = ('file_name', 'case', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('file_name', 'case__case_id')
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('Caso', {'fields': ('case',)}),
        ('Documento', {'fields': ('document_type', 'file', 'file_name')}),
        ('Auditoría', {'fields': ('uploaded_by', 'uploaded_at')}),
    )


@admin.register(SecondOpinion)
class SecondOpinionAdmin(admin.ModelAdmin):
    """Admin para el modelo SecondOpinion"""
    
    list_display = ('case', 'doctor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('case__case_id', 'doctor__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Caso', {'fields': ('case',)}),
        ('Médico', {'fields': ('doctor',)}),
        ('Opinión', {'fields': ('opinion_text', 'recommendations')}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(CaseAuditLog)
class CaseAuditLogAdmin(admin.ModelAdmin):
    """Admin para el modelo CaseAuditLog"""
    
    list_display = ('case', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('case__case_id', 'user__email')
    readonly_fields = ('case', 'user', 'action', 'description', 'timestamp', 'ip_address')
    
    def has_add_permission(self, request):
        """No permitir agregar registros de auditoría manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar registros de auditoría"""
        return False
    
    fieldsets = (
        ('Caso', {'fields': ('case',)}),
        ('Usuario', {'fields': ('user', 'ip_address')}),
        ('Acción', {'fields': ('action', 'description')}),
        ('Auditoría', {'fields': ('timestamp',)}),
    )


@admin.register(MedicalOpinion)
class MedicalOpinionAdmin(admin.ModelAdmin):
    """Admin para el modelo MedicalOpinion"""
    
    list_display = ('case', 'doctor', 'voto', 'fecha_emision')
    list_filter = ('voto', 'fecha_emision')
    search_fields = ('case__case_id', 'doctor__nombres', 'doctor__apellidos')
    readonly_fields = ('fecha_emision', 'actualizado_en')
    
    fieldsets = (
        ('Caso', {'fields': ('case',)}),
        ('Médico', {'fields': ('doctor',)}),
        ('Votación', {'fields': ('voto', 'comentario_privado')}),
        ('Auditoría', {'fields': ('fecha_emision', 'actualizado_en')}),
    )


@admin.register(FinalReport)
class FinalReportAdmin(admin.ModelAdmin):
    """Admin para el modelo FinalReport"""
    
    list_display = ('case', 'conclusion', 'redactado_por', 'fecha_emision')
    list_filter = ('conclusion', 'fecha_emision')
    search_fields = ('case__case_id', 'redactado_por__nombres')
    readonly_fields = ('fecha_emision', 'actualizado_en', 'firma_electronica')
    
    fieldsets = (
        ('Caso', {'fields': ('case',)}),
        ('Contenido', {'fields': ('conclusion', 'justificacion', 'recomendaciones')}),
        ('Responsable', {'fields': ('redactado_por',)}),
        ('Archivo', {'fields': ('pdf_file', 'firma_electronica')}),
        ('Auditoría', {'fields': ('fecha_emision', 'actualizado_en')}),
    )


# === Admin para nuevos modelos MDT ===

@admin.register(MDTMessage)
class MDTMessageAdmin(admin.ModelAdmin):
    list_display = ('caso', 'autor', 'tipo', 'creado_en')
    list_filter = ('tipo', 'creado_en')
    search_fields = ('caso__case_id', 'autor__nombres', 'contenido')
    readonly_fields = ('creado_en', 'actualizado_en')


@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'caso', 'estado', 'ultimo_heartbeat')
    list_filter = ('estado',)
    search_fields = ('usuario__nombres', 'caso__case_id')


@admin.register(AlgoritmoConfig)
class AlgoritmoConfigAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ponderacion_carga', 'modo_estricto', 'activo')
    list_editable = ('activo',)
    fieldsets = (
        ('General', {'fields': ('nombre', 'activo')}),
        ('Ponderación', {'fields': ('ponderacion_carga', 'modo_estricto')}),
        ('Límites', {'fields': ('limite_mensual_por_medico', 'permitir_overrides', 'respetar_disponibilidad')}),
    )


@admin.register(AsignacionAuditLog)
class AsignacionAuditLogAdmin(admin.ModelAdmin):
    list_display = ('caso', 'medico_seleccionado', 'decision', 'creado_en')
    list_filter = ('decision', 'creado_en')
    search_fields = ('caso__case_id', 'medico_seleccionado__nombres')
    readonly_fields = ('creado_en',)


@admin.register(ConsensusWorkflow)
class ConsensusWorkflowAdmin(admin.ModelAdmin):
    list_display = ('caso', 'fase', 'votos_a_favor', 'votos_en_contra', 'fecha_inicio')
    list_filter = ('fase',)
    search_fields = ('caso__case_id',)
    readonly_fields = ('fecha_inicio', 'fecha_consenso')


@admin.register(ConsensusVote)
class ConsensusVoteAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'medico', 'voto', 'creado_en')
    list_filter = ('voto',)
    search_fields = ('medico__nombres',)


@admin.register(ClinicalTemplate)
class ClinicalTemplateAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'tipo_cancer', 'es_global', 'veces_usada', 'esta_activa')
    list_filter = ('es_global', 'especialidad')
    search_fields = ('nombre', 'contenido')


@admin.register(AnatomicalRegion)
class AnatomicalRegionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'activo')
    list_editable = ('activo',)
    filter_horizontal = ('especialidades_sugeridas',)


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tema', 'idioma', 'notificaciones_email')
    fieldsets = (
        ('Usuario', {'fields': ('usuario',)}),
        ('Apariencia', {'fields': ('tema', 'idioma')}),
        ('Notificaciones', {'fields': ('notificaciones_email', 'notificaciones_push')}),
    )
