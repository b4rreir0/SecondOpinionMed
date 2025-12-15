from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import PacienteRegistrationForm

def landing_page(request):
    return render(request, 'public/landing.html')

def login_view(request):
    if request.method == 'POST':
        # Lógica de login
        pass
    return render(request, 'public/login.html')

def logout_view(request):
    # Lógica de logout
    pass

def register_view(request):
    if request.method == 'POST':
        form = PacienteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('pacientes:dashboard')
    else:
        form = PacienteRegistrationForm()
    return render(request, 'public/register.html', {'form': form})

def terminos(request):
    return render(request, 'public/terminos.html')

def privacidad(request):
    return render(request, 'public/privacidad.html')

def contacto(request):
    return render(request, 'public/contacto.html')

def como_funciona(request):
    return render(request, 'public/como_funciona.html')
