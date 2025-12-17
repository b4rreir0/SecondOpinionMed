from django.contrib import admin
from .models import Case, CaseDocument, SecondOpinion, CaseAuditLog


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
