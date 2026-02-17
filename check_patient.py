#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.get(email='germanbarreiro2121@gmail.com')

print("=== Usuario ===")
print(f"Email: {u.email}")
print(f"First name: {u.first_name}")
print(f"Last name: {u.last_name}")

print("\n=== PatientProfile ===")
if hasattr(u, 'patient_profile'):
    pp = u.patient_profile
    print(f"Nombre: {pp.nombre}")
    print(f"Apellidos: {pp.apellidos}")
    print(f"Fecha nacimiento: {pp.fecha_nacimiento}")
    print(f"Genero: {pp.genero}")
    print(f"Telefono: {pp.telefono}")
else:
    print("No tiene patient_profile")
