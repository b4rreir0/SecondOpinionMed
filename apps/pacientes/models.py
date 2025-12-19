# pacientes/models.py
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from core.models import TimeStampedModel
from django.utils import timezone
import uuid

class Paciente(TimeStampedModel):
    """Modelo principal del paciente"""
    ESTADOS_CIVILES = (
        ('soltero', 'Soltero/a'),
        ('casado', 'Casado/a'),
        ('divorciado', 'Divorciado/a'),
        ('viudo', 'Viudo/a'),
        ('union_libre', 'Unión Libre'),
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
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paciente')
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO, default='cc')
    numero_documento = models.CharField(max_length=20, unique=True, validators=[
        RegexValidator(regex=r'^\d+$', message='Solo números permitidos')
    ])
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=20, choices=GENEROS)
    estado_civil = models.CharField(max_length=20, choices=ESTADOS_CIVILES, default='soltero')
    
    # Información de contacto
    telefono = models.CharField(max_length=15, validators=[
        RegexValidator(regex=r'^\+?[\d\s\-\(\)]+$', message='Formato de teléfono inválido')
    ])
    telefono_alternativo = models.CharField(max_length=15, blank=True, validators=[
        RegexValidator(regex=r'^\+?[\d\s\-\(\)]+$', message='Formato de teléfono inválido')
    ])
    email_alternativo = models.EmailField(blank=True)
    
    # Información médica básica
    eps = models.CharField(max_length=100, verbose_name='EPS')
    regimen = models.CharField(max_length=50, choices=[
        ('contributivo', 'Contributivo'),
        ('subsidiado', 'Subsidiado'),
        ('especial', 'Especial'),
        ('excepcion', 'Excepción'),
    ])
    grupo_sanguineo = models.CharField(max_length=10, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ], blank=True)
    
    # Información adicional
    ocupacion = models.CharField(max_length=100, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    
    # Consentimientos y autorizaciones
    consentimiento_datos = models.BooleanField(default=False)
    autorizacion_tratamiento = models.BooleanField(default=False)
    fecha_consentimiento = models.DateTimeField(null=True, blank=True)
    
    # Estado del paciente
    activo = models.BooleanField(default=True)
    fecha_inactivacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['apellidos', 'nombres']
        indexes = [
            models.Index(fields=['numero_documento']),
            models.Index(fields=['nombres', 'apellidos']),
            models.Index(fields=['activo']),
        ]
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def edad(self):
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.numero_documento}"

class AntecedenteMedico(TimeStampedModel):
    """Antecedentes médicos del paciente"""
    TIPOS = (
        ('personal', 'Antecedente Personal'),
        ('familiar', 'Antecedente Familiar'),
        ('quirurgico', 'Antecedente Quirúrgico'),
        ('alergia', 'Alergia'),
        ('medicamento', 'Medicamento'),
        ('habito', 'Hábito'),
    )
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='antecedentes')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField()
    fecha_diagnostico = models.DateField(null=True, blank=True)
    medico_tratante = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_diagnostico']
    
    def __str__(self):
        return f"{self.paciente.nombre_completo} - {self.get_tipo_display()}"

class CasoClinico(TimeStampedModel):
    """Caso clínico para segunda opinión"""
    ESTADOS = (
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('asignado', 'Asignado'),
        ('en_revision', 'En Revisión'),
        ('comite', 'En Comité'),
        ('concluido', 'Concluido'),
        ('cancelado', 'Cancelado'),
    )
    
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='casos')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    diagnostico_actual = models.TextField()
    tratamiento_actual = models.TextField(blank=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    
    # Fechas importantes
    fecha_sintomas = models.DateField(null=True, blank=True)
    fecha_diagnostico = models.DateField(null=True, blank=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    fecha_conclusion = models.DateTimeField(null=True, blank=True)
    
    # Asignaciones
    medico_asignado = models.ForeignKey('medicos.Medico', on_delete=models.SET_NULL, null=True, blank=True)
    # Localidad representada por el caso (se asigna al crear la solicitud)
    localidad = models.ForeignKey('medicos.Localidad', on_delete=models.SET_NULL, null=True, blank=True, related_name='casos')
    comite_asignado = models.ForeignKey('medicos.ComiteMultidisciplinario', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Archivos adjuntos
    documentos_clinicos = models.ManyToManyField('DocumentoClinico', blank=True)
    
    # Metadatos
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    notas_admin = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['prioridad']),
            models.Index(fields=['paciente']),
            models.Index(fields=['uuid']),
        ]
    
    def asignar_medico(self, medico):
        from medicos.models import Medico
        if isinstance(medico, Medico):
            self.medico_asignado = medico
            self.estado = 'asignado'
            self.fecha_asignacion = timezone.now()
            self.save()
    
    def enviar_a_comite(self, comite):
        from medicos.models import ComiteMultidisciplinario
        if isinstance(comite, ComiteMultidisciplinario):
            self.comite_asignado = comite
            self.estado = 'comite'
            self.save()
    
    def __str__(self):
        return f"Caso {self.uuid} - {self.paciente.nombre_completo}"

class DocumentoClinico(TimeStampedModel):
    """Documentos clínicos adjuntos a casos"""
    TIPOS = (
        ('historia_clinica', 'Historia Clínica'),
        ('examenes', 'Exámenes de Laboratorio'),
        ('imagenes', 'Imágenes Diagnósticas'),
        ('informes', 'Informes Médicos'),
        ('consentimiento', 'Consentimiento Informado'),
        ('otro', 'Otro'),
    )
    
    caso = models.ForeignKey(CasoClinico, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=30, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='documentos/casos/%Y/%m/')
    descripcion = models.TextField(blank=True)
    confidencial = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-creado_en']
    
    def __str__(self):
        return f"{self.titulo} - {self.caso.uuid}"

class SolicitudSegundaOpinion(TimeStampedModel):
    """Solicitud formal de segunda opinión"""
    caso = models.OneToOneField(CasoClinico, on_delete=models.CASCADE, related_name='solicitud')
    motivo_solicitud = models.TextField()
    especialidad_solicitada = models.CharField(max_length=100)
    urgencia = models.BooleanField(default=False)
    autorizacion_eps = models.BooleanField(default=False)
    numero_autorizacion = models.CharField(max_length=50, blank=True)
    
    # Información del médico remitente
    medico_remitente = models.CharField(max_length=100)
    institucion_remitente = models.CharField(max_length=100)
    contacto_remitente = models.CharField(max_length=100)
    
    # Estado de la solicitud
    aprobado = models.BooleanField(default=False)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Solicitud {self.caso.uuid} - {self.especialidad_solicitada}"
