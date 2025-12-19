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
    path('document/download/<int:doc_id>/', views.download_document, name='download_document'),
    # SOP creation flow (include sop URL patterns from urls_sop)
    path('', include('cases.urls_sop')),
]
