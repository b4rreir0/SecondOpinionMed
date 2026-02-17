from django.contrib import admin
from .models import (
    Especialidad, 
    TipoCancer, 
    Medico, 
    Localidad, 
    MedicalGroup, 
    DoctorGroupMembership,
    ComiteMultidisciplinario
)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)


@admin.register(TipoCancer)
class TipoCancerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'especialidad_principal', 'activo')
    list_filter = ('activo', 'especialidad_principal')
    search_fields = ('nombre', 'codigo')


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'registro_medico', 'estado', 'disponible_segundas_opiniones', 'casos_actuales')
    list_filter = ('estado', 'disponible_segundas_opiniones', 'especialidades')
    search_fields = ('nombres', 'apellidos', 'registro_medico', 'numero_documento')
    filter_horizontal = ('especialidades',)


@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'medico')
    search_fields = ('nombre',)


@admin.register(MedicalGroup)
class MedicalGroupAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_cancer', 'quorum_config', 'activo', 'numero_miembros')
    list_filter = ('activo', 'tipo_cancer')
    search_fields = ('nombre',)


@admin.register(DoctorGroupMembership)
class DoctorGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('medico', 'grupo', 'es_responsable', 'activo', 'fecha_union')
    list_filter = ('activo', 'es_responsable', 'grupo')
    search_fields = ('medico__nombres', 'medico__apellidos', 'grupo__nombre')


@admin.register(ComiteMultidisciplinario)
class ComiteMultidisciplinarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'min_medicos', 'max_casos_simultaneos', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
