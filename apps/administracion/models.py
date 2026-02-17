# administracion/models.py
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel

class Administrador(TimeStampedModel):
    """Modelo del administrador del sistema"""
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
    )
    
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='administrador')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email_institucional = models.EmailField()
    telefono = models.CharField(max_length=15)
    
    # Información profesional
    cargo = models.CharField(max_length=100, default='Administrador')
    departamento = models.CharField(max_length=100, default='TI')
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    # Permisos especiales
    puede_gestionar_usuarios = models.BooleanField(default=True)
    puede_configurar_sistema = models.BooleanField(default=False)
    puede_ver_auditoria = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['apellidos', 'nombres']
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.cargo}"

class ConfiguracionSistema(TimeStampedModel):
    """Configuraciones generales del sistema"""
    TIPOS = (
        ('general', 'General'),
        ('seguridad', 'Seguridad'),
        ('notificaciones', 'Notificaciones'),
        ('algoritmos', 'Algoritmos'),
        ('integraciones', 'Integraciones'),
    )
    
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='general')
    descripcion = models.TextField(blank=True)
    editable = models.BooleanField(default=True)
    requiere_restart = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['tipo', 'clave']
    
    def __str__(self):
        return f"{self.clave} - {self.get_tipo_display()}"

class ReporteSistema(TimeStampedModel):
    """Reportes generados por el sistema"""
    TIPOS = (
        ('estadistico', 'Estadístico'),
        ('auditoria', 'Auditoría'),
        ('rendimiento', 'Rendimiento'),
        ('seguridad', 'Seguridad'),
        ('uso', 'Uso del Sistema'),
    )
    
    FRECUENCIAS = (
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
    )
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIAS)
    
    # Configuración
    parametros = models.JSONField(default=dict)
    activo = models.BooleanField(default=True)
    
    # Ejecución
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    proxima_ejecucion = models.DateTimeField(null=True, blank=True)
    ejecuciones_exitosas = models.PositiveIntegerField(default=0)
    ejecuciones_fallidas = models.PositiveIntegerField(default=0)
    
    # Resultados
    ultimo_resultado = models.TextField(blank=True)
    archivo_reporte = models.FileField(upload_to='reportes/sistema/%Y/%m/', null=True, blank=True)
    
    class Meta:
        ordering = ['tipo', 'frecuencia', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

class NotificacionSistema(TimeStampedModel):
    """Notificaciones del sistema"""
    TIPOS = (
        ('sistema', 'Sistema'),
        ('mantenimiento', 'Mantenimiento'),
        ('seguridad', 'Seguridad'),
        ('actualizacion', 'Actualización'),
        ('alerta', 'Alerta'),
    )
    
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    )
    
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    
    # Destinatarios
    destinatarios = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='notificaciones_recibidas', blank=True)
    roles_destinatarios = models.ManyToManyField('auth.Group', related_name='notificaciones', blank=True)
    
    # Estado
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notificaciones_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def marcar_como_leida(self, usuario=None):
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()}"

class BackupSistema(TimeStampedModel):
    """Registro de backups del sistema"""
    TIPOS = (
        ('completo', 'Backup Completo'),
        ('base_datos', 'Base de Datos'),
        ('archivos', 'Archivos'),
        ('configuracion', 'Configuración'),
    )
    
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('ejecutando', 'Ejecutando'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
    )
    
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField(blank=True)
    
    # Ejecución
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    archivo_backup = models.FileField(upload_to='backups/%Y/%m/', null=True, blank=True)
    tamano_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Metadatos
    ejecutado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    checksum = models.CharField(max_length=128, blank=True)
    ubicacion_almacenamiento = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
    
    @property
    def duracion(self):
        if self.fecha_inicio and self.fecha_fin:
            return self.fecha_fin - self.fecha_inicio
        return None
    
    @property
    def tamano_mb(self):
        if self.tamano_bytes:
            return round(self.tamano_bytes / (1024 * 1024), 2)
        return None
    
    def iniciar_backup(self):
        self.estado = 'ejecutando'
        self.fecha_inicio = timezone.now()
        self.save()
    
    def completar_backup(self):
        self.estado = 'completado'
        self.fecha_fin = timezone.now()
        self.save()
    
    def marcar_fallido(self):
        self.estado = 'fallido'
        self.fecha_fin = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Backup {self.nombre} - {self.get_tipo_display()}"

class LogSistema(TimeStampedModel):
    """Logs del sistema"""
    NIVELES = (
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    )
    
    nivel = models.CharField(max_length=20, choices=NIVELES)
    mensaje = models.TextField()
    modulo = models.CharField(max_length=100)
    funcion = models.CharField(max_length=100, blank=True)
    linea = models.PositiveIntegerField(null=True, blank=True)
    
    # Contexto
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Excepción (si aplica)
    excepcion_tipo = models.CharField(max_length=100, blank=True)
    excepcion_mensaje = models.TextField(blank=True)
    traceback = models.TextField(blank=True)
    
    # Metadatos
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['nivel']),
            models.Index(fields=['modulo']),
        ]
    
    def __str__(self):
        return f"[{self.get_nivel_display()}] {self.modulo}: {self.mensaje[:50]}"
