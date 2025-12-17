# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
import django
import sys
from .models import ModuloSistema, Especialidad, Institucion
from administracion.models import ConfiguracionSistema
from .decorators import admin_required
from .forms import EspecialidadForm, InstitucionForm

@login_required
def mantenimiento(request):
    """Página de mantenimiento del sistema"""
    return render(request, 'core/mantenimiento.html')

@admin_required
@require_http_methods(["POST"])
def toggle_modulo(request, modulo_id):
    """Activar/desactivar módulo del sistema"""
    try:
        modulo = ModuloSistema.objects.get(id=modulo_id)
        modulo.activa = not modulo.activa
        modulo.save()
        
        status = "activado" if modulo.activa else "desactivado"
        messages.success(request, f'Módulo {modulo.nombre} {status} exitosamente.')
        
        return JsonResponse({
            'success': True,
            'status': status,
            'modulo': modulo.nombre
        })
    except ModuloSistema.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Módulo no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@admin_required
def configuracion_update(request):
    """Actualizar configuración del sistema vía AJAX"""
    if request.method == 'POST':
        clave = request.POST.get('clave')
        valor = request.POST.get('valor')
        
        try:
            config, created = ConfiguracionSistema.objects.get_or_create(
                clave=clave,
                defaults={'valor': valor, 'tipo': 'general'}
            )
            
            if not created:
                config.valor = valor
                config.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración actualizada exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

@login_required
def api_health_check(request):
    """Endpoint para verificar salud del sistema"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'user': request.user.username if request.user.is_authenticated else None
    })

@admin_required
def system_info(request):
    """Información del sistema para administradores"""
    # Información básica del sistema
    info = {
        'django_version': django.get_version(),
        'python_version': sys.version,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'debug_mode': settings.DEBUG,
        'installed_apps': len(settings.INSTALLED_APPS),
        'total_users': User.objects.count(),
        'active_modules': ModuloSistema.objects.filter(estado='activo').count(),
    }
    
    return JsonResponse(info)

# API endpoints para AJAX
@login_required
@require_http_methods(["GET"])
def especialidades_api(request):
    """API para obtener especialidades en formato JSON"""
    especialidades = Especialidad.objects.filter(estado='activa').values('id', 'nombre')
    return JsonResponse(list(especialidades), safe=False)

@login_required
@require_http_methods(["GET"])
def instituciones_api(request):
    """API para obtener instituciones en formato JSON"""
    instituciones = Institucion.objects.filter(estado='activa').values('id', 'nombre', 'tipo')
    return JsonResponse(list(instituciones), safe=False)

# Views genéricas para Especialidades
class EspecialidadListView(ListView):
    """Lista de especialidades"""
    model = Especialidad
    template_name = 'core/especialidad_list.html'
    context_object_name = 'especialidades'
    paginate_by = 20
    
    def get_queryset(self):
        return Especialidad.objects.all().order_by('nombre')

class EspecialidadDetailView(DetailView):
    """Detalle de especialidad"""
    model = Especialidad
    template_name = 'core/especialidad_detail.html'
    context_object_name = 'especialidad'

class EspecialidadCreateView(CreateView):
    """Crear nueva especialidad"""
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'core/especialidad_form.html'
    success_url = reverse_lazy('core:especialidad_list')
    
    @admin_required
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class EspecialidadUpdateView(UpdateView):
    """Actualizar especialidad"""
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'core/especialidad_form.html'
    success_url = reverse_lazy('core:especialidad_list')
    
    @admin_required
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class EspecialidadDeleteView(DeleteView):
    """Eliminar especialidad"""
    model = Especialidad
    template_name = 'core/especialidad_confirm_delete.html'
    success_url = reverse_lazy('core:especialidad_list')
    
    @admin_required
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

# Views genéricas para Instituciones
class InstitucionListView(ListView):
    """Lista de instituciones"""
    model = Institucion
    template_name = 'core/institucion_list.html'
    context_object_name = 'instituciones'
    paginate_by = 20
    
    def get_queryset(self):
        return Institucion.objects.all().order_by('nombre')

class InstitucionDetailView(DetailView):
    """Detalle de institución"""
    model = Institucion
    template_name = 'core/institucion_detail.html'
    context_object_name = 'institucion'

class InstitucionCreateView(CreateView):
    """Crear nueva institución"""
    model = Institucion
    form_class = InstitucionForm
    template_name = 'core/institucion_form.html'
    success_url = reverse_lazy('core:institucion_list')
    
    @admin_required
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class InstitucionUpdateView(UpdateView):
    """Actualizar institución"""
    model = Institucion
    form_class = InstitucionForm
    template_name = 'core/institucion_form.html'
    success_url = reverse_lazy('core:institucion_list')
    
    @admin_required
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class InstitucionDeleteView(DeleteView):
    """Eliminar institución"""
    model = Institucion
    template_name = 'core/institucion_confirm_delete.html'
    success_url = reverse_lazy('core:institucion_list')
    
    @admin_required
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

# Vistas de perfil de usuario
@login_required
def perfil_usuario(request):
    """Mostrar perfil del usuario actual"""
    return render(request, 'core/perfil.html', {'usuario': request.user})

@login_required
def editar_perfil(request):
    """Editar perfil del usuario"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('core:perfil')
    
    return render(request, 'core/editar_perfil.html', {'usuario': request.user})

@login_required
def cambiar_password(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        from django.contrib.auth import update_session_auth_hash
        from django.contrib.auth.forms import PasswordChangeForm
        
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('core:perfil')
        else:
            for field, errors in form.errors.items():
                messages.error(request, f'{field}: {", ".join(errors)}')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'core/cambiar_password.html', {'form': form})

# Vistas de error personalizadas
def handler404(request, exception):
    """Vista para error 404"""
    return render(request, 'core/404.html', status=404)

def handler500(request):
    """Vista para error 500"""
    return render(request, 'core/500.html', status=500)

def handler403(request, exception):
    """Vista para error 403"""
    return render(request, 'core/403.html', status=403)

def handler400(request, exception):
    """Vista para error 400"""
    return render(request, 'core/400.html', status=400)
