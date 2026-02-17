from django.urls import path, include
from . import views

# application namespace for this urls module
app_name = 'cases'

urlpatterns = [
    # Dashboards
    path('patients/dashboard/', views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('patients/case/<str:case_id>/', views.PatientCaseDetailView.as_view(), name='patient_case_detail'),
    
    path('doctors/dashboard/', views.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('doctors/case/<str:case_id>/', views.DoctorCaseDetailView.as_view(), name='doctor_case_detail'),
    
    # Vistas de médicos - Casos
    path('doctors/casos-pendientes/', views.CasosPendientesView.as_view(), name='casos_pendientes'),
    path('doctors/mis-casos/', views.MisCasosView.as_view(), name='mis_casos'),
    path('doctors/reportes/', views.ReportesView.as_view(), name='reportes'),
    
    # Chat MDT
    path('doctors/chat/', views.MDTChatView.as_view(), name='mdt_chat'),
    
    # Guía del Sistema
    path('doctors/guia/', views.GuiaSistemaView.as_view(), name='guia_sistema'),
    
    # Vistas MDT - Opiniones
    path('doctors/case/<str:case_id>/opinion/', views.MedicalOpinionCreateView.as_view(), name='opinion_form'),
    path('doctors/case/<str:case_id>/cerrar-votacion/', views.CerrarVotacionView.as_view(), name='cerrar_votacion'),
    
    # Vistas MDT - Votación y Respuesta Final
    path('doctors/case/<str:case_id>/mdt-opinion/', views.MDTOpinionView.as_view(), name='mdt_opinion'),
    path('doctors/case/<str:case_id>/mdt-response/', views.MDTFinalResponseView.as_view(), name='mdt_response'),
    
    # Vistas MDT - Informes
    path('doctors/case/<str:case_id>/report/', views.FinalReportCreateView.as_view(), name='report_form'),
    
    # Documentos
    path('document/download/<int:doc_id>/', views.download_document, name='download_document'),
    
    # Consentimiento informado
    path('consentimiento/', views.consentimiento_informado_view, name='consentimiento_info'),
    
    # SOP creation flow (include sop URL patterns from urls_sop)
    path('', include('cases.urls_sop')),
]
