# public/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from .forms import RegistroUsuarioForm, LoginForm, ContactoForm

def home(request):
    """Vista de la página principal"""
    if request.user.is_authenticated:
        return redirect('public:dashboard')
    
    return render(request, 'public/home.html')

def about(request):
    """Vista de la página 'Acerca de'"""
    return render(request, 'public/about.html')

def services(request):
    """Vista de servicios ofrecidos"""
    return render(request, 'public/services.html')

def contact(request):
    """Vista de contacto"""
    if request.method == 'POST':
        # Procesar formulario de contacto
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Aquí iría la lógica para enviar email o guardar en BD
        messages.success(request, 'Mensaje enviado exitosamente. Nos pondremos en contacto pronto.')
        return redirect('public:contact')
    
    return render(request, 'public/contact.html')

@csrf_protect
def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('public:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}')
            
            # Redirigir según el rol
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('public:dashboard')
        else:
            messages.error(request, 'Credenciales inválidas. Por favor, inténtelo de nuevo.')
    
    return render(request, 'public/login.html')

def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('public:home')

@login_required
def dashboard(request):
    """Dashboard principal según el rol del usuario"""
    context = {}
    
    if hasattr(request.user, 'paciente'):
        return redirect('pacientes:dashboard')
    elif hasattr(request.user, 'medico'):
        return redirect('medicos:dashboard')
    elif hasattr(request.user, 'administrador'):
        return redirect('administracion:dashboard')
    else:
        # Usuario sin rol específico
        messages.warning(request, 'Su cuenta no tiene un rol asignado. Contacte al administrador.')
        return redirect('public:home')
    
    return render(request, 'public/dashboard.html', context)

@csrf_protect
def register_paciente(request):
    """Registro de pacientes"""
    if request.user.is_authenticated:
        return redirect('public:dashboard')
    
    if request.method == 'POST':
        form = PacienteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada exitosamente. Bienvenido al sistema.')
            return redirect('pacientes:dashboard')
    else:
        form = PacienteRegistrationForm()
    
    return render(request, 'public/register_paciente.html', {'form': form})

@csrf_protect
def register_medico(request):
    """Registro de médicos"""
    if request.user.is_authenticated:
        return redirect('public:dashboard')
    
    if request.method == 'POST':
        form = MedicoRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cuenta de médico creada exitosamente. Su cuenta será revisada por un administrador.')
            return redirect('public:login')
    else:
        form = MedicoRegistrationForm()
    
    return render(request, 'public/register_medico.html', {'form': form})

@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """Solicitud de restablecimiento de contraseña"""
    if request.user.is_authenticated:
        return redirect('public:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        # Aquí iría la lógica para enviar email de restablecimiento
        messages.success(request, 'Si el email existe en nuestro sistema, recibirás instrucciones para restablecer tu contraseña.')
        return redirect('public:login')
    
    return render(request, 'public/password_reset.html')

def privacy_policy(request):
    """Política de privacidad"""
    return render(request, 'public/privacy_policy.html')

def terms_of_service(request):
    """Términos de servicio"""
    return render(request, 'public/terms_of_service.html')

def faq(request):
    """Preguntas frecuentes"""
    return render(request, 'public/faq.html')

@csrf_protect
def registro_view(request):
    """Vista de registro general de usuarios"""
    if request.user.is_authenticated:
        return redirect('public:dashboard')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada exitosamente. Bienvenido al sistema.')
            return redirect('public:dashboard')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'public/registro.html', {'form': form})
