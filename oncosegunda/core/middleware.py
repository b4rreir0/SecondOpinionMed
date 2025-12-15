# core/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from pacientes.models import Paciente
from medicos.models import Medico
from administracion.models import Administrador

class RoleRedirectMiddleware:
    """Middleware que redirige usuarios según su rol después del login"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Solo redirigir si está en la página de login o home genérica
            if request.path in ['/login/', '/admin/login/', '/', '/home/']:
                if hasattr(request.user, 'paciente') and request.user.paciente.activo:
                    return redirect('pacientes:dashboard')
                elif hasattr(request.user, 'medico') and request.user.medico.estado == 'activo':
                    return redirect('medicos:dashboard')
                elif hasattr(request.user, 'administrador') and request.user.administrador.estado == 'activo':
                    return redirect('administracion:dashboard')
        
        response = self.get_response(request)
        return response

class ModuleAccessMiddleware:
    """Middleware que verifica acceso a módulos del sistema"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Verificar módulos activos
            from core.models import ModuloSistema
            
            # Mapear URLs a módulos
            module_mapping = {
                '/pacientes/': 'pacientes',
                '/medicos/': 'medicos', 
                '/administracion/': 'administracion',
            }
            
            for url_prefix, module_name in module_mapping.items():
                if request.path.startswith(url_prefix):
                    try:
                        modulo = ModuloSistema.objects.get(nombre=module_name)
                        if not modulo.activa:
                            messages.error(request, f'El módulo {modulo.nombre} está temporalmente inactivo.')
                            return redirect('public:dashboard')
                    except ModuloSistema.DoesNotExist:
                        # Módulo no configurado, permitir acceso
                        pass
        
        response = self.get_response(request)
        return response

class AuditMiddleware:
    """Middleware que registra actividad de usuarios para auditoría"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Actualizar último acceso para médicos y administradores
            if hasattr(request.user, 'medico'):
                request.user.medico.ultimo_acceso = timezone.now()
                request.user.medico.save(update_fields=['ultimo_acceso'])
            elif hasattr(request.user, 'administrador'):
                request.user.administrador.ultimo_acceso = timezone.now()
                request.user.administrador.save(update_fields=['ultimo_acceso'])
        
        response = self.get_response(request)
        
        # Registrar acciones importantes
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'DELETE']:
            from core.services import AuditoriaService
            
            # Solo registrar acciones críticas
            critical_paths = [
                '/admin/', '/pacientes/casos/', '/medicos/revisiones/',
                '/administracion/configuracion/', '/administracion/usuarios/'
            ]
            
            if any(path in request.path for path in critical_paths):
                action_type = {
                    'POST': 'creacion',
                    'PUT': 'modificacion', 
                    'DELETE': 'eliminacion'
                }.get(request.method, 'acceso')
                
                AuditoriaService.registrar_accion(
                    usuario=request.user,
                    tipo_accion=action_type,
                    modelo_afectado='Sistema',
                    descripcion=f"Acceso a {request.path}",
                    ip_address=self.get_client_ip(request)
                )
        
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SecurityHeadersMiddleware:
    """Middleware que añade headers de seguridad"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Headers de seguridad básicos
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy básica
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        response['Content-Security-Policy'] = csp
        
        return response

class MaintenanceModeMiddleware:
    """Middleware para modo mantenimiento"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar si el sistema está en mantenimiento
        from core.models import ConfiguracionSistema
        
        try:
            mantenimiento = ConfiguracionSistema.objects.get(clave='modo_mantenimiento')
            if mantenimiento.valor.lower() == 'true':
                # Permitir acceso a administradores y páginas de login
                if (hasattr(request.user, 'administrador') or 
                    request.path in ['/admin/login/', '/login/', '/mantenimiento/'] or
                    request.path.startswith('/static/') or request.path.startswith('/media/')):
                    return self.get_response(request)
                else:
                    from django.shortcuts import render
                    return render(request, 'core/mantenimiento.html', status=503)
        except ConfiguracionSistema.DoesNotExist:
            pass
        
        return self.get_response(request)