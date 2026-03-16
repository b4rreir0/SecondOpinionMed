#!/usr/bin/env python
# Script para mostrar grupos médicos, tipos de cáncer y miembros
from django.core.management.base import BaseCommand
from apps.medicos.models import MedicalGroup, DoctorGroupMembership, TipoCancer


class Command(BaseCommand):
    help = 'Muestra los grupos médicos, tipos de cáncer y sus integrantes'
    
    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('GRUPOS MÉDICOS DEFINIDOS EN EL SISTEMA')
        self.stdout.write('=' * 70)
        
        grupos = MedicalGroup.objects.all()
        if not grupos:
            self.stdout.write(self.style.WARNING('No hay grupos médicos definidos.'))
        else:
            for grupo in grupos:
                self.stdout.write(f'\n📋 Grupo: {grupo.nombre}')
                self.stdout.write(f'   Descripción: {grupo.descripcion or "Sin descripción"}')
                self.stdout.write(f'   Activo: {"Sí" if grupo.activo else "No"}')
                
                # Tipos de cáncer
                tipos = grupo.tipos_cancer.all()
                if tipos:
                    self.stdout.write('   Tipos de cáncer que atiende:')
                    for tc in tipos:
                        self.stdout.write(f'      • {tc.nombre} ({tc.codigo})')
                else:
                    self.stdout.write('   Tipos de cáncer: Sin tipos asignados')
                
                # Miembros
                membresias = DoctorGroupMembership.objects.filter(grupo=grupo, activo=True)
                if membresias:
                    self.stdout.write(f'   Integrantes ({membresias.count()}):')
                    for m in membresias:
                        rol_display = m.get_rol_display()
                        self.stdout.write(f'      • Dr. {m.medico.nombre_completo} - {rol_display}')
                else:
                    self.stdout.write('   Integrantes: Sin miembros asignados')
                self.stdout.write('-' * 70)
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('TIPOS DE CÁNCER DEFINIDOS EN EL SISTEMA')
        self.stdout.write('=' * 70)
        tipos_cancer = TipoCancer.objects.all()
        for tc in tipos_cancer:
            grupo_asignado = tc.grupo_medico
            if grupo_asignado:
                grupos_str = grupo_asignado.nombre
            else:
                grupos_str = 'Sin grupo asignado'
            self.stdout.write(f'• {tc.nombre} ({tc.codigo}) -> {grupos_str}')
