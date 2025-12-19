# core/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
import uuid

class TimeStampedModel(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Especialidad(models.Model):
    """Modelo para especialidades médicas"""
    ESTADOS = (
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
    )
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'Especialidades'
    
    def __str__(self):
        return self.nombre

class Institucion(models.Model):
    """Modelo para instituciones médicas"""
    TIPOS = (
        ('hospital', 'Hospital'),
        ('clinica', 'Clínica'),
        ('centro_salud', 'Centro de Salud'),
        ('consultorio', 'Consultorio'),
        ('otro', 'Otro'),
    )
    
    ESTADOS = (
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
    )
    
    nombre = models.CharField(max_length=200, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    responsable = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activa')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'Instituciones'
    
    def __str__(self):
        return self.nombre

class ModuloSistema(models.Model):
    """Modelo para gestionar módulos del sistema"""
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('mantenimiento', 'En Mantenimiento'),
    )
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    version = models.CharField(max_length=20, default='1.0')
    fecha_activacion = models.DateTimeField(auto_now_add=True)
    fecha_desactivacion = models.DateTimeField(null=True, blank=True)
    dependencias = models.ManyToManyField('self', symmetrical=False, blank=True)
    
    def activar(self):
        self.estado = 'activo'
        self.fecha_desactivacion = None
        self.save()
    
    def desactivar(self):
        self.estado = 'inactivo'
        self.fecha_desactivacion = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.nombre} v{self.version}"

class AlgoritmoConfig(models.Model):
    """Configuración de algoritmos del sistema"""
    TIPOS = (
        ('asignacion', 'Asignación de Casos'),
        ('notificacion', 'Notificaciones'),
        ('prioridad', 'Priorización'),
    )
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    configuracion = models.JSONField(default=dict)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['nombre', 'tipo']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

class Auditoria(models.Model):
    """Registro de auditoría del sistema"""
    TIPOS_ACCION = (
        ('creacion', 'Creación'),
        ('modificacion', 'Modificación'),
        ('eliminacion', 'Eliminación'),
        ('acceso', 'Acceso'),
        ('sistema', 'Sistema'),
    )
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo_accion = models.CharField(max_length=20, choices=TIPOS_ACCION)
    modelo_afectado = models.CharField(max_length=100)
    objeto_id = models.IntegerField(null=True, blank=True)
    descripcion = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['usuario', 'fecha']),
        ]
    
    def __str__(self):
        return f"{self.usuario} - {self.get_tipo_accion_display()} - {self.modelo_afectado}"
