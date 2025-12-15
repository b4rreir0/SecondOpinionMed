from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing_page'),

    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Recuperación de contraseña
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='public/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='public/password_reset_done.html'
         ),
         name='password_reset_done'),

    # Páginas informativas
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('contacto/', views.contacto, name='contacto'),
    path('como-funciona/', views.como_funciona, name='como_funciona'),
]