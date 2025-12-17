from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.PatientRegistrationView.as_view(), name='register_patient'),
    path('verification-pending/', views.VerificationPendingView.as_view(), name='verification_pending'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
]
