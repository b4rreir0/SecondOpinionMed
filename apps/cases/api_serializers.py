"""
Serializers API para los modelos MDT.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Case, CaseDocument, MedicalOpinion, FinalReport
from .mdt_models import (
    MDTMessage, UserPresence, AlgoritmoConfig, AsignacionAuditLog,
    ConsensusWorkflow, ConsensusVersion, ConsensusVote, OpinionDisidente,
    ClinicalTemplate, AnatomicalRegion, UserPreferences
)
from medicos.models import Medico, MedicalGroup, DoctorGroupMembership, Especialidad, TipoCancer

User = get_user_model()


# ===================
# Serializers de Médico
# ===================

class MedicoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='nombre_completo', read_only=True)
    especialidades_nombres = serializers.SerializerMethodField()
    
    class Meta:
        model = Medico
        fields = [
            'id', 'nombre_completo', 'numero_documento', 'registro_medico',
            'especialidades', 'especialidades_nombres', 'institucion_actual',
            'estado', 'disponible_segundas_opiniones', 'max_casos_mes',
            'casos_actuales', 'fecha_ingreso'
        ]
    
    def get_especialidades_nombres(self, obj):
        return [e.nombre for e in obj.especialidades.all()]


# ===================
# Serializers de Grupo Médico
# ===================

class MedicalGroupSerializer(serializers.ModelSerializer):
    tipo_cancer_nombre = serializers.CharField(source='tipo_cancer.nombre', read_only=True)
    numero_miembros = serializers.IntegerField(source='numero_miembros', read_only=True)
    miembros = MedicoSerializer(many=True, read_only=True)
    
    class Meta:
        model = MedicalGroup
        fields = [
            'id', 'nombre', 'tipo_cancer', 'tipo_cancer_nombre', 'descripcion',
            'responsable_por_defecto', 'quorum_config', 'activo',
            'numero_miembros', 'miembros'
        ]


class DoctorGroupMembershipSerializer(serializers.ModelSerializer):
    medico = MedicoSerializer(read_only=True)
    grupo = MedicalGroupSerializer(read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    
    class Meta:
        model = DoctorGroupMembership
        fields = [
            'id', 'medico', 'grupo', 'rol', 'rol_display',
            'es_responsable', 'puede_votar', 'puede_declara_consenso',
            'disponible_asignacion_auto', 'activo', 'fecha_union'
        ]


# ===================
# Serializers de Caso
# ===================

class CaseListSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    doctor_nombre = serializers.CharField(source='doctor.medico.nombre_completo', read_only=True)
    medical_group_nombre = serializers.CharField(source='medical_group.nombre', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Case
        fields = [
            'id', 'case_id', 'patient', 'patient_email', 'doctor', 'doctor_nombre',
            'medical_group', 'medical_group_nombre', 'primary_diagnosis',
            'specialty_required', 'tipo_cancer', 'estadio', 'status', 'status_display',
            'created_at', 'assigned_at', 'fecha_limite', 'completed_at'
        ]


class CaseDetailSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    doctor = MedicoSerializer(read_only=True)
    medical_group = MedicalGroupSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documentos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Case
        fields = [
            'id', 'case_id', 'patient', 'patient_email', 'doctor', 'medical_group',
            'responsable', 'primary_diagnosis', 'specialty_required', 'tipo_cancer',
            'estadio', 'description', 'tratamiento_propuesto_original',
            'objetivo_consulta', 'diagnosis_date', 'localidad',
            'status', 'status_display', 'created_at', 'updated_at',
            'assigned_at', 'fecha_limite', 'completed_at', 'documentos_count'
        ]
    
    def get_documentos_count(self, obj):
        return obj.documents.count()


# ===================
# Serializers de Mensajería MDT
# ===================

class MDTMessageSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.CharField(source='autor.nombre_completo', read_only=True)
    leido_por_nombres = serializers.SerializerMethodField()
    
    class Meta:
        model = MDTMessage
        fields = [
            'id', 'caso', 'grupo', 'autor', 'autor_nombre', 'tipo',
            'contenido', 'mensaje_padre', 'es_privado', 'esta_editado',
            'leido_por_nombres', 'creado_en', 'actualizado_en'
        ]
    
    def get_leido_por_nombres(self, obj):
        return [m.nombre_completo for m in obj.leido_por.all()]


# ===================
# Serializers de Presencia
# ===================

class UserPresenceSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    esta_activo = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserPresence
        fields = [
            'id', 'usuario', 'usuario_nombre', 'caso', 'estado',
            'ultimo_heartbeat', 'esta_activo', 'ip_address'
        ]


# ===================
# Serializers de Algoritmo
# ===================

class AlgoritmoConfigSerializer(serializers.ModelSerializer):
    modificado_por_email = serializers.EmailField(source='modificado_por.email', read_only=True)
    
    class Meta:
        model = AlgoritmoConfig
        fields = [
            'id', 'nombre', 'ponderacion_carga', 'modo_estricto',
            'limite_mensual_por_medico', 'permitir_overrides',
            'respetar_disponibilidad', 'activo', 'modificado_por_email',
            'creado_en', 'actualizado_en'
        ]


class AsignacionAuditLogSerializer(serializers.ModelSerializer):
    caso_case_id = serializers.CharField(source='caso.case_id', read_only=True)
    medico_nombre = serializers.CharField(source='medico_seleccionado.nombre_completo', read_only=True)
    decision_display = serializers.CharField(source='get_decision_display', read_only=True)
    override_por_email = serializers.EmailField(source='override_por.email', read_only=True)
    
    class Meta:
        model = AsignacionAuditLog
        fields = [
            'id', 'caso', 'caso_case_id', 'medico_seleccionado', 'medico_nombre',
            'decision', 'decision_display', 'motivo', 'score_carga',
            'score_antiguedad', 'score_final', 'config', 'es_override',
            'override_justificacion', 'override_por_email', 'creado_en'
        ]


# ===================
# Serializers de Consenso
# ===================

class ConsensusWorkflowSerializer(serializers.ModelSerializer):
    caso_case_id = serializers.CharField(source='caso.case_id', read_only=True)
    fase_display = serializers.CharField(source='get_fase_display', read_only=True)
    nivel_evidencia_display = serializers.CharField(source='get_nivel_evidencia_display', read_only=True)
    
    class Meta:
        model = ConsensusWorkflow
        fields = [
            'id', 'caso', 'caso_case_id', 'fase', 'fase_display',
            'propuesta_consenso', 'votos_a_favor', 'votos_en_contra',
            'abstenciones', 'nivel_evidencia', 'nivel_evidencia_display',
            'requiere_mas_informacion', 'descripcion_info_requerida',
            'fecha_limite_info', 'fecha_inicio', 'fecha_consenso',
            'esta_bloqueado', 'creado_en'
        ]


class ConsensusVoteSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico.nombre_completo', read_only=True)
    voto_display = serializers.CharField(source='get_voto_display', read_only=True)
    
    class Meta:
        model = ConsensusVote
        fields = [
            'id', 'workflow', 'medico', 'medico_nombre',
            'voto', 'voto_display', 'justificacion', 'creado_en'
        ]


class ConsensusVersionSerializer(serializers.ModelSerializer):
    modificado_por_nombre = serializers.CharField(source='modificado_por.nombre_completo', read_only=True)
    
    class Meta:
        model = ConsensusVersion
        fields = [
            'id', 'workflow', 'numero_version', 'contenido',
            'modificado_por', 'modificado_por_nombre',
            'notas_cambio', 'creado_en'
        ]


class OpinionDisidenteSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico.nombre_completo', read_only=True)
    
    class Meta:
        model = OpinionDisidente
        fields = [
            'id', 'workflow', 'medico', 'medico_nombre',
            'opinion', 'creado_en'
        ]


# ===================
# Serializers de Plantillas
# ===================

class ClinicalTemplateSerializer(serializers.ModelSerializer):
    especialidad_nombre = serializers.CharField(source='especialidad.nombre', read_only=True)
    tipo_cancer_nombre = serializers.CharField(source='tipo_cancer.nombre', read_only=True)
    creador_nombre = serializers.CharField(source='creador.nombre_completo', read_only=True)
    
    class Meta:
        model = ClinicalTemplate
        fields = [
            'id', 'nombre', 'especialidad', 'especialidad_nombre',
            'tipo_cancer', 'tipo_cancer_nombre', 'contenido',
            'es_global', 'creador', 'creador_nombre', 'esta_activa',
            'veces_usada', 'creado_en'
        ]


class AnatomicalRegionSerializer(serializers.ModelSerializer):
    especialidades_sugeridas_nombres = serializers.SerializerMethodField()
    
    class Meta:
        model = AnatomicalRegion
        fields = [
            'id', 'nombre', 'codigo', 'descripcion',
            'svg_path', 'svg_id', 'especialidades_sugeridas',
            'especialidades_sugeridas_nombres', 'sintomas_asociados', 'activo'
        ]
    
    def get_especialidades_sugeridas_nombres(self, obj):
        return [e.nombre for e in obj.especialidades_sugeridas.all()]


# ===================
# Serializers de Preferencias
# ===================

class UserPreferencesSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    tema_display = serializers.CharField(source='get_tema_display', read_only=True)
    
    class Meta:
        model = UserPreferences
        fields = [
            'id', 'usuario', 'usuario_email', 'tema', 'tema_display',
            'idioma', 'notificaciones_email', 'notificaciones_push',
            'elementos_por_pagina'
        ]


# ===================
# Serializers de Opiniones
# ===================

class MedicalOpinionSerializer(serializers.ModelSerializer):
    doctor_nombre = serializers.CharField(source='doctor.nombre_completo', read_only=True)
    caso_case_id = serializers.CharField(source='caso.case_id', read_only=True)
    voto_display = serializers.CharField(source='get_voto_display', read_only=True)
    
    class Meta:
        model = MedicalOpinion
        fields = [
            'id', 'caso', 'caso_case_id', 'doctor', 'doctor_nombre',
            'voto', 'voto_display', 'comentario_privado',
            'fecha_emision', 'actualizado_en'
        ]
