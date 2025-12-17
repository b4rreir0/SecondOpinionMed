from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, PatientProfile, DoctorProfile


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Admin para el modelo CustomUser"""
    
    list_display = ('email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name')}),
        ('Rol y Permisos', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
    
    ordering = ('email',)


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """Admin para el modelo PatientProfile"""
    
    list_display = ('full_name', 'identity_document', 'user_email', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('full_name', 'identity_document', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email del Usuario'
    
    fieldsets = (
        ('Usuario', {'fields': ('user',)}),
        ('Identificación Personal (PHI)', {'fields': ('full_name', 'identity_document', 'phone_number', 'date_of_birth')}),
        ('Información Médica (PHI)', {'fields': ('primary_diagnosis', 'medical_history', 'current_treatment')}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """Admin para el modelo DoctorProfile"""
    
    list_display = ('full_name', 'medical_license', 'specialty', 'is_available', 'created_at')
    list_filter = ('specialty', 'is_available', 'created_at')
    search_fields = ('full_name', 'medical_license', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Usuario', {'fields': ('user',)}),
        ('Información Profesional', {'fields': ('full_name', 'medical_license', 'specialty', 'phone_number', 'institution')}),
        ('Disponibilidad', {'fields': ('is_available', 'max_concurrent_cases')}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )
