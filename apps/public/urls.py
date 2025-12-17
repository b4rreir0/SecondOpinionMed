# public/urls.py
from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),

    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),

    # Páginas informativas
    path('acerca/', views.about, name='acerca'),
    path('servicios/', views.services, name='servicios'),
    path('contacto/', views.contact, name='contacto'),

    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('privacidad/', views.privacy_policy, name='privacidad'),
    path('terminos/', views.terms_of_service, name='terminos'),
    path('faq/', views.faq, name='faq'),
]