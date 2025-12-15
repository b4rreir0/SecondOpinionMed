from django.contrib import admin
from .models import Patient, Specialty, UserProfile, Case, Assignment, CallLog

# Register your models here.

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_index')
    filter_horizontal = ('responsibles',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    filter_horizontal = ('specialties',)

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'specialty', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'specialty')
    search_fields = ('patient__first_name', 'patient__last_name')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('case', 'assigned_to', 'assigned_at')
    list_filter = ('assigned_at',)

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('case', 'caller', 'call_date')
    list_filter = ('call_date',)
    search_fields = ('caller__username', 'case__id')
