# medicos/models.py
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from core.models import TimeStampedModel
import uuid
from django.utils import timezone

class Especialidad(models.Model):
    """Especialidades médicas"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Medico(TimeStampedModel):
    """Modelo del médico especialista"""
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
    )
    
    GENEROS = (
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro'),
    )
    
    TIPOS_DOCUMENTO = (
        ('cc', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('ti', 'Tarjeta de Identidad'),
        ('pasaporte', 'Pasaporte'),
    )
    
    # Información básica
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medico')
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO, default='cc')
    numero_documento = models.CharField(max_length=20, unique=True, validators=[
        RegexValidator(regex=r'^\d+$', message='Solo números permitidos')
    ])
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=20, choices=GENEROS)
    
    # Información profesional
    registro_medico = models.CharField(max_length=20, unique=True, verbose_name='Registro Médico')
    especialidades = models.ManyToManyField(Especialidad, related_name='medicos')
    experiencia_anios = models.PositiveIntegerField(default=0)
    institucion_actual = models.CharField(max_length=100)
    
    # Información de contacto
    telefono = models.CharField(max_length=15, validators=[
        RegexValidator(regex=r'^\+?[\d\s\-\(\)]+$', message='Formato de teléfono inválido')
    ])
    telefono_alternativo = models.CharField(max_length=15, blank=True, validators=[
        RegexValidator(regex=r'^\+?[\d\s\-\(\)]+$', message='Formato de teléfono inválido')
    ])
    email_institucional = models.EmailField(blank=True)
    
    # Estado y disponibilidad
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    disponible_segundas_opiniones = models.BooleanField(default=True)
    max_casos_mes = models.PositiveIntegerField(default=10)
    casos_actuales = models.PositiveIntegerField(default=0)
    
    # Estadísticas
    casos_revisados = models.PositiveIntegerField(default=0)
    casos_comite = models.PositiveIntegerField(default=0)
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Metadatos
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['apellidos', 'nombres']
        indexes = [
            models.Index(fields=['numero_documento']),
            models.Index(fields=['registro_medico']),
            models.Index(fields=['estado']),
            models.Index(fields=['disponible_segundas_opiniones']),
        ]
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def especialidades_principales(self):
        return ", ".join([esp.nombre for esp in self.especialidades.all()[:3]])
    
    @property
    def capacidad_disponible(self):
        return max(0, self.max_casos_mes - self.casos_actuales)
    
    def actualizar_casos(self, incremento=1):
        self.casos_actuales += incremento
        self.casos_revisados += incremento
        self.save()
    
    def __str__(self):
        return f"Dr. {self.nombre_completo} - {self.registro_medico}"


class Localidad(TimeStampedModel):
    """Localidad/territorio asignado a un médico"""
    nombre = models.CharField(max_length=200, unique=True)
    medico = models.ForeignKey(Medico, on_delete=models.SET_NULL, null=True, blank=True, related_name='localidades')

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class ComiteMultidisciplinario(TimeStampedModel):
    """Comité multidisciplinario para casos complejos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    especialidades_requeridas = models.ManyToManyField(Especialidad, related_name='comites')
    medicos_miembros = models.ManyToManyField(Medico, related_name='comites', blank=True)
    
    # Configuración
    min_medicos = models.PositiveIntegerField(default=3)
    max_casos_simultaneos = models.PositiveIntegerField(default=5)
    casos_actuales = models.PositiveIntegerField(default=0)
    
    # Estado
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nombre']
    
    @property
    def miembros_activos(self):
        return self.medicos_miembros.filter(estado='activo', disponible_segundas_opiniones=True)
    
    @property
    def capacidad_disponible(self):
        return max(0, self.max_casos_simultaneos - self.casos_actuales)
    
    def puede_asignar_caso(self):
        return self.activo and self.miembros_activos.count() >= self.min_medicos and self.capacidad_disponible > 0
    
    def __str__(self):
        return f"Comité {self.nombre}"

class RevisionCaso(TimeStampedModel):
    """Revisión médica de un caso clínico"""
    TIPOS_REVISION = (
        ('individual', 'Revisión Individual'),
        ('comite', 'Revisión en Comité'),
    )
    
    caso = models.ForeignKey('pacientes.CasoClinico', on_delete=models.CASCADE, related_name='revisiones')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='revisiones')
    tipo_revision = models.CharField(max_length=20, choices=TIPOS_REVISION, default='individual')
    
    # Contenido de la revisión
    diagnostico_propuesto = models.TextField()
    tratamiento_recomendado = models.TextField()
    observaciones = models.TextField(blank=True)
    conclusiones = models.TextField(blank=True)
    
    # Evaluación
    coincidencia_diagnostico = models.BooleanField(default=False)
    cambio_tratamiento = models.BooleanField(default=False)
    requiere_discusion = models.BooleanField(default=False)
    
    # Estado
    completada = models.BooleanField(default=False)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    
    # Archivo de informe
    informe_pdf = models.FileField(upload_to='informes/revisiones/%Y/%m/', null=True, blank=True)
    
    class Meta:
        ordering = ['-creado_en']
        unique_together = ['caso', 'medico']
    
    def completar_revision(self):
        self.completada = True
        self.fecha_completada = timezone.now()
        self.save()
        self.medico.actualizar_casos()
    
    def __str__(self):
        return f"Revisión {self.caso.uuid} - Dr. {self.medico.nombre_completo}"

class ReunionComite(TimeStampedModel):
    """Reunión de comité multidisciplinario"""
    ESTADOS = (
        ('programada', 'Programada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    )
    
    comite = models.ForeignKey(ComiteMultidisciplinario, on_delete=models.CASCADE, related_name='reuniones')
    caso = models.ForeignKey('pacientes.CasoClinico', on_delete=models.CASCADE, related_name='reuniones_comite')
    
    # Detalles de la reunión
    fecha_programada = models.DateTimeField()
    duracion_estimada = models.PositiveIntegerField(default=60, help_text='Duración en minutos')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programada')
    
    # Participantes
    medicos_participantes = models.ManyToManyField(Medico, related_name='reuniones_participadas', blank=True)
    moderador = models.ForeignKey(Medico, on_delete=models.SET_NULL, null=True, related_name='reuniones_moderadas')
    
    # Resultados
    conclusiones = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    acta_reunion = models.FileField(upload_to='actas/comite/%Y/%m/', null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_programada']
    
    def iniciar_reunion(self):
        self.estado = 'en_curso'
        self.fecha_inicio = timezone.now()
        self.save()
    
    def completar_reunion(self):
        self.estado = 'completada'
        self.fecha_fin = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Reunión Comité {self.comite.nombre} - {self.caso.uuid}"

class DisponibilidadMedico(TimeStampedModel):
    """Disponibilidad semanal del médico"""
    DIAS_SEMANA = (
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    )
    
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='disponibilidad')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['medico', 'dia_semana', 'hora_inicio', 'hora_fin']
    
    def __str__(self):
        return f"{self.medico.nombre_completo} - {self.get_dia_semana_display()}"
