"""
URL configuration for SecondOpinionMed project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from public.views import landing_page

urlpatterns = [
    # Páginas públicas
    path('', landing_page, name='landing_page'),
    path('login/', include('public.urls')),
    path('register/', include('public.urls')),

    # Módulo de pacientes
    path('paciente/', include('pacientes.urls')),

    # Módulo de médicos
    path('medico/', include('medicos.urls')),

    # Módulo de administración
    path('admin/', include('administracion.urls')),

    # Admin de Django (opcional - puedes deshabilitarlo)
    path('django-admin/', admin.site.urls),

    # API REST (comentado hasta implementar)
    # path('api/', include('api.urls')),
]

# Para servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
