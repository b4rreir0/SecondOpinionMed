from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('register/<uuid:token>/', views.DoctorRegisterView.as_view(), name='doctor_register'),
]
