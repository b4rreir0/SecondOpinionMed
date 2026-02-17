# 🏥 SISTEMA DE SEGUNDAS OPINIONES MÉDICAS - MDT

## Arquitectura Django Pura (Segunda Opinión Médica)

---

## 📋 VISIÓN GENERAL

Sistema profesional para comités multidisciplinarios médicos (MDT - Multidisciplinary Team) donde:

- **Pacientes** solicitan evaluación de casos oncológicos
- **Grupos médicos** (ej: Comité de Pulmón) evalúan colaborativamente
- **Todos los miembros** emiten opiniones individuales desde el inicio
- **Médico responsable** coordina, consolida votaciones y redacta informe final
- **Administrador** gestiona la plataforma (sin intervención clínica)
- **Todo se procesa en Django**: templates HTML, vistas CBV, formularios nativos

---

## 🗄️ ALMACENAMIENTO DE ARCHIVOS (Sistema Propio)

En lugar de AWS S3, el sistema usa **almacenamiento local con estructura organizada**:

```
media/
├── casos/
│   └── {case_id}/
│       ├── documentos/           # Documentos subidos por pacientes/médicos
│       │   ├── {uuid}_informe_hospital.pdf
│       │   ├── {uuid}_biopsia.jpg
│       │   └── {uuid}_resonancia.dcm
│       └── informes/             # PDFs generados por el sistema
│           └── {case_id}_informe_final.pdf
├── temp/                         # Archivos temporales para procesamiento
└── plantillas/                   # Plantillas PDF base (si usas WeasyPrint)
```

**Configuración en `settings.py`:**

```python
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Almacenamiento local (se puede migrar a MinIO posteriormente)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
```

---

## 👥 ROLES Y PERMISOS

| Rol | Descripción | Permisos Clave |
|-----|-------------|----------------|
| **Paciente** | Usuario que solicita segunda opinión | Crear casos, ver sus casos, descargar informes finales |
| **Médico** | Especialista que evalúa casos | Ver casos de sus comités, emitir opiniones, ver documentos |
| **Administrador** | Administrador de la plataforma | CRUD usuarios, comités, configuración |

### Implementación en [`apps/authentication/models.py`](apps/authentication/models.py:14):

```python
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Paciente'),
        ('doctor', 'Médico'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    is_active = models.BooleanField(default=False)  # Se activa tras verificación de email
    email_verified = models.BooleanField(default=False)
```

---

## 🗃️ MODELOS DE DATOS PRINCIPALES

### 1. Usuarios y Perfiles

#### CustomUser ([`apps/authentication/models.py`](apps/authentication/models.py:14))
```python
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
```

#### PatientProfile ([`apps/authentication/models.py`](apps/authentication/models.py:66))
```python
class PatientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    full_name = EncryptedCharField(max_length=255)  # CIFRADO
    identity_document = EncryptedCharField(max_length=50)  # CIFRADO
    phone_number = EncryptedCharField(max_length=20)  # CIFRADO
    date_of_birth = models.DateField(null=True, blank=True)
```

#### DoctorProfile ([`apps/medicos/models.py`](apps/medicos/models.py:21))
```python
class Medico(TimeStampedModel):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    numero_documento = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    registro_medico = models.CharField(max_length=20, unique=True)
    especialidades = models.ManyToManyField(Especialidad)
    institucion_actual = models.CharField(max_length=100)
    disponible_segundas_opiniones = models.BooleanField(default=True)
    max_casos_mes = models.PositiveIntegerField(default=10)
    casos_actuales = models.PositiveIntegerField(default=0)
```

---

### 2. Especialidades y Localidades

#### Especialidad ([`apps/medicos/models.py`](apps/medicos/models.py:9))
```python
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
```

#### Localidad ([`apps/medicos/models.py`](apps/medicos/models.py:XXX))
```python
class Localidad(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    departamento = models.CharField(max_length=100)
```

---

### 3. Casos y Estados

#### Case ([`apps/cases/models.py`](apps/cases/models.py:24))
```python
class Case(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('SUBMITTED', 'Enviado'),
        ('PROCESSING', 'Procesando'),
        ('PAID', 'Pagado'),
        ('IN_REVIEW', 'En Revisión'),
        ('OPINION_COMPLETE', 'Opinión Completa'),
        ('CLOSED', 'Cerrado'),
        ('CANCELLED', 'Cancelado'),
    )
    
    patient = models.ForeignKey('authentication.CustomUser', related_name='patient_cases')
    doctor = models.ForeignKey('authentication.CustomUser', null=True, blank=True, related_name='doctor_cases')
    
    case_id = models.CharField(max_length=50, unique=True)  # "CASO-2025-0001"
    primary_diagnosis = EncryptedCharField(max_length=255)  # CIFRADO
    specialty_required = models.CharField(max_length=100)
    description = EncryptedTextField()  # CIFRADO
    diagnosis_date = models.DateField(null=True, blank=True)
    localidad = models.ForeignKey('medicos.Localidad', null=True, blank=True)
    
    status = FSMField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

---

### 4. Documentos

#### CaseDocument ([`apps/cases/models.py`](apps/cases/models.py:XXX))
```python
class CaseDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('informe', 'Informe Médico'),
        ('imagen', 'Imagen Diagnóstica'),
        ('laboratorio', 'Resultado de Laboratorio'),
        ('otros', 'Otros Documentos'),
    )
    
    case = models.ForeignKey(Case, related_name='documentos')
    file = models.FileField(upload_to='cases/documents/%Y/%m/%d/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    is_anonymized = models.BooleanField(default=False)
    s3_file_path = models.CharField(max_length=500, blank=True)  # Ruta en S3 si se usa
    uploaded_by = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 5. Auditoría

El sistema usa **django-auditlog** para registrar todas las acciones:

```python
# Configuración en settings.py
INSTALLED_APPS += ['auditlog']
AUDITLOG_LOGENTRY_MODEL = 'auditlog.LogEntry'

# Modelos auditados automáticamente
# Case, CaseDocument, CustomUser, Medico, Paciente
```

---

## 🔄 FLUJO DE TRABAJO (Workflow)

### Paso 1: Solicitud del Paciente

1. **Paciente** completa formulario web (Django Template + Crispy Forms)
2. Adjunta documentos médicos (múltiples archivos)
3. Guarda como borrador (`DRAFT`) o envía (`SUBMITTED`)

### Paso 2: Asignación Automática (Señal Django)

```
Trigger: Caso pasa a SUBMITTED
↓
Sistema determina Especialidad requerida
↓
Algoritmo round-robin selecciona médico responsable
↓
Crea CaseAssignment para el médico
↓
Envía emails de notificación (tarea Celery)
↓
Estado: PROCESSING
```

**Implementación del algoritmo** ([`apps/cases/services.py`](apps/cases/services.py)):

```python
def asignar_caso_automatico(case):
    """
    1. Determina especialista según specialty_required
    2. Selecciona médico por round-robin (menos casos activos)
    3. Asigna caso al médico
    4. Envía notificaciones
    """
    especialidad = Especialidad.objects.filter(
        nombre__icontains=case.specialty_required
    ).first()
    
    if not especialidad:
        # Notificar a coordinación
        return
    
    # Seleccionar médico con menos casos activos
    medico = Medico.objects.filter(
        especialidades=especialidad,
        disponible_segundas_opiniones=True,
        estado='activo'
    ).annotate(
        casos_activos=Count('usuario__doctor_cases', 
            filter=Q(usuario__doctor_cases__status__in=['PROCESSING', 'IN_REVIEW']))
    ).order_by('casos_activos').first()
    
    if medico:
        case.doctor = medico.usuario
        case.status = 'PROCESSING'
        case.assigned_at = timezone.now()
        case.save()
        
        # Notificar al médico
        notificar_nuevo_caso.delay(medico.usuario.id, case.id)
```

### Paso 3: Revisión del Médico

- **Médico** revisa caso y documentos
- Puede solicitar información adicional al paciente
- Puede escalar a revisión por comité (futuro)
- Genera informe preliminar

### Paso 4: Cierre del Caso

```
Trigger: Médico completa análisis
↓
Genera opinión/descripción del caso
↓
Guarda en Case.description (actualizado)
↓
Estado: OPINION_COMPLETED
↓
Notifica al paciente
↓
Estado: CLOSED
```

---

## 🎨 FRONTEND (Django Templates)

### Estructura de Templates

```
templates/
├── base.html                    # Layout principal con Bootstrap 5
├── base_patient.html            # Extiende base, menú paciente
├── base_doctor.html             # Extiende base, menú médico
├── components/
│   ├── navbar.html
│   ├── sidebar.html
│   ├── notification_bell.html
│   └── case_status_badge.html
├── authentication/
│   ├── login.html
│   ├── register.html
│   └── password_reset.html
├── patients/
│   ├── dashboard.html           # Lista de casos del paciente
│   ├── case_form.html           # Crear/editar solicitud
│   └── case_detail.html         # Ver caso + documentos
├── doctors/
│   ├── dashboard.html           # Casos asignados
│   ├── case_detail.html         # Ver caso + documentos
│   └── case_list.html           # Lista de casos
└── administration/
    └── dashboard.html           # Panel admin
```

### Tecnologías Frontend

- **Bootstrap 5**: Grid, componentes, utilidades
- **django-crispy-forms**: Renderizado elegante de formularios
- **django-ckeditor**: Editor WYSIWYG (opcional para informes)
- **HTMX** (opcional): Para actualizaciones dinámicas sin recargar página
- **Alpine.js** (opcional): Para interactividad simple

### Ejemplo de Vista (Class-Based View)

```python
# apps/cases/views.py
from django.views.generic import DetailView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q

class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = 'cases/case_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        if user.is_patient():
            return Case.objects.filter(patient=user).order_by('-created_at')
        elif user.is_doctor():
            return Case.objects.filter(doctor=user).order_by('-created_at')
        return Case.objects.none()
```

---

## ⚙️ LÓGICA DE NEGOCIO (Services/Utils)

### Servicio de Asignación ([`apps/cases/services.py`](apps/cases/services.py))

```python
def asignar_caso_automatico(case):
    """
    Algoritmo de asignación round-robin:
    1. Determina especialidad según tipo_cancer
    2. Selecciona médico con menos casos activos
    3. Asigna caso
    4. Envía notificaciones
    """
    # Implementación completa en services.py
    pass

def get_proximo_medico_por_especialidad(especialidad):
    """
    Round-robin: médico con menos casos activos
    """
    medicos = Medico.objects.filter(
        especialidades=especialidad,
        disponible_segundas_opiniones=True,
        estado='activo'
    ).annotate(
        casos_activos=Count('usuario__doctor_cases', 
            filter=Q(usuario__doctor_cases__status__in=['PROCESSING', 'IN_REVIEW']))
    ).order_by('casos_activos', 'usuario__date_joined')
    
    return medicos.first()
```

---

## 🔒 SEGURIDAD Y CUMPLIMIENTO

| Aspecto | Implementación |
|---------|---------------|
| **Cifrado datos sensibles** | `django-fernet-fields` en campos clínicos |
| **Permisos a nivel objeto** | `django-guardian` (médico solo ve sus casos) |
| **Auditoría completa** | `django-auditlog` en todos los modelos críticos |
| **Autenticación** | Django auth con verificación de email |
| **Protección CSRF/XSS** | Middleware nativo de Django |
| **Roles** | CustomUser con roles patient/doctor |

### Configuración de Seguridad ([`oncosegunda/settings.py`](oncosegunda/settings.py))

```python
# Middleware de seguridad
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Permisos de objeto
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'authentication.CustomUser'
```

---

## 🚀 INFRAESTRUCTURA Y DEPENDENCIAS

### Dependencias Principales ([`requirements.txt`](requirements.txt))

```
# Core
django>=6.0
python>=3.11

# Formularios y Templates
django-crispy-forms
crispy-bootstrap5
django-ckeditor

# Estado y Permisos
django-fsm
django-guardian
django-auditlog

# Cifrado
django-fernet-fields

# Tareas Asíncronas
celery
redis

# Base de datos
psycopg2-binary  # PostgreSQL

# Almacenamiento
boto3  # AWS S3 (opcional)

# Procesamiento
pillow
pydicom
PyPDF2

# Utilidades
python-magic
python-dotenv
djangorestframework
django-extensions
```

### Arquitectura de Servicios

```
┌─────────────────┐
│   Nginx         │ ← Reverse proxy, sirve static/media
└────────┬────────┘
         │
┌────────▼────────┐
│   Gunicorn      │ ← Servidor WSGI
│   Django App    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐   ┌▼────────┐
│PostgreSQL│   │  Redis    │
│  (Datos) │   │ (Caché/   │
│          │   │  Cola Celery)
└──────────┘   └─────────┘
         │
    ┌────▼────┐
    │  Celery │ ← Workers para tareas asíncronas
    │ Workers │   (emails, procesamiento)
    └─────────┘
```

---

## 📊 PANELES POR ROL

### Paciente

```
┌─────────────────────────────────────┐
│  MI DASHBOARD                       │
├─────────────────────────────────────┤
│  [Nueva Solicitud]                  │
│                                     │
│  MIS CASOS:                         │
│  ┌─────────────────────────────┐   │
│  │ CASO-2025-0001              │   │
│  │ Especialidad: Pulmón        │   │
│  │ Estado: [En evaluación]     │   │
│  │ Fecha: 15/02/2025          │   │
│  │ [Ver detalle]               │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Médico

```
┌─────────────────────────────────────┐
│  PANEL MÉDICO                       │
├─────────────────────────────────────┤
│  CASOS ASIGNADOS: 3                 │
│  ┌─────────────────────────────┐   │
│  │ CASO-2025-0002 (Pulmón)    │   │
│  │ Paciente: Juan Pérez       │   │
│  │ Estado: En Revisión        │   │
│  │ [Ver caso]                 │   │
│  └─────────────────────────────┘   │
│                                     │
│  ESTADÍSTICAS:                      │
│  Casos revisados: 15               │
│  Casos este mes: 3                │
└─────────────────────────────────────┘
```

---

## ✅ ESTRUCTURA DEL PROYECTO

```
SecondOpinionMed/
├── apps/
│   ├── authentication/    # Usuarios, roles, perfiles
│   ├── pacientes/         # Módulo pacientes
│   ├── medicos/          # Módulo médicos/especialistas
│   ├── cases/            # Casos de segunda opinión
│   ├── documents/        # Manejo de documentos
│   ├── notifications/   # Notificaciones email/in-app
│   ├── public/          # Páginas públicas
│   ├── administracion/  # Panel de administración
│   └── core/            # Utilidades compartidas
├── oncosegunda/         # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── templates/            # Templates HTML
├── static/              # Archivos CSS, JS, imágenes
├── media/               # Archivos subidos
├── docs/                # Documentación
├── scripts/             # Scripts de utilidad
├── nginx/               # Configuración Nginx
├── requirements.txt
├── manage.py
└── docker-compose.yml
```

---

## 📋 RESUMEN DE FUNCIONALIDADES ACTUALES

### Funcionalidades Implementadas

| Módulo | Funcionalidad | Estado |
|--------|---------------|--------|
| **Authentication** | Registro de usuarios | ✅ |
| | Login/Logout | ✅ |
| | Verificación de email | ✅ |
| | Perfiles cifrados | ✅ |
| **Pacientes** | Crear solicitud | ✅ |
| | Subir documentos | ✅ |
| | Ver estado de casos | ✅ |
| | Dashboard | ✅ |
| **Médicos** | Ver casos asignados | ✅ |
| | Revisar casos | ✅ |
| | Dashboard | ✅ |
| **Cases** | Estados FSM | ✅ |
| | Asignación automática | ✅ |
| | Documentos | ✅ |
| | Auditoría | ✅ |
| **Notifications** | Emails | ✅ |
| | Tareas Celery | ✅ |
| **Administración** | Panel Django Admin | ✅ |
| | Gestión de usuarios | ✅ |

---

## 🎯 MODELO DE DATOS ACTUAL

### Relaciones entre Modelos

```
CustomUser (role: patient/doctor)
    │
    ├── PatientProfile (1:1) ← CIFRADO
    │
    └── Medico (1:1)
            │
            ├── Especialidad (M:N)
            │
            └── Localidad (FK)
    
Case
    ├── patient (FK → CustomUser)
    ├── doctor (FK → CustomUser)
    ├── CaseDocument (1:N)
    ├── localidad (FK → Localidad)
    └── STATUS_FSM (DRAFT → SUBMITTED → PROCESSING → IN_REVIEW → OPINION_COMPLETE → CLOSED)
```

---

## 🔄 FLUJO DE DATOS ACTUAL

```
Paciente              Sistema                 Médico
   │                      │                      │
   │──Registrar─────────▶│                      │
   │                      │                      │
   │──Crear Caso────────▶│                      │
   │   (SUBMITTED)       │                      │
   │                      │                      │
   │                      │──Asignar───────────▶│
   │                      │   (PROCESSING)      │
   │                      │                      │
   │                      │──Notificar─────────▶│
   │                      │                      │
   │                      │◀──Revisar───────────│
   │                      │   (IN_REVIEW)        │
   │                      │                      │
   │                      │◀──Completar──────────│
   │                      │   (OPINION_COMPLETE) │
   │                      │                      │
   │◀─Notificar──────────│                      │
   │                      │                      │
   │◀─Ver resultado──────│                      │
   │                      │                      │
   │                      │──Cerrar─────────────▶│
   │                      │   (CLOSED)           │
```

---

## 📦 MODELOS CLAVE ACTUALES

### Case (Estados FSM)

| Estado | Descripción | Transiciones |
|--------|-------------|---------------|
| DRAFT | Borrador | → SUBMITTED |
| SUBMITTED | Enviado | → PROCESSING |
| PROCESSING | Asignado al médico | → IN_REVIEW |
| IN_REVIEW | En revisión médica | → OPINION_COMPLETE |
| OPINION_COMPLETE | Opinión completada | → CLOSED |
| CLOSED | Caso cerrado | - |
| CANCELLED | Cancelado | - |

---

## 🛠️ TECHNOLOGÍAS USADAS

| Categoría | Tecnología |
|-----------|------------|
| Framework | Django 6.0 |
| Python | 3.11+ |
| Base de datos | PostgreSQL (producción), SQLite (dev) |
| Cache/Colas | Redis + Celery |
| Templates | Django Templates + Bootstrap 5 |
| Formularios | Crispy Forms |
| Permisos | Django Guardian |
| Auditoría | Django Auditlog |
| Estado | Django FSM |
| Cifrado | Fernet Fields |
| API | Django REST Framework |
| Server | Gunicorn + Nginx |
| Container | Docker |

---

## 🚧 ROADMAP FUTURO

- [ ] Sistema de Comités Multidisciplinarios (MDT)
- [ ] Sistema de Votaciones entre médicos
- [ ] Generación de PDF con WeasyPrint
- [ ] Editor WYSIWYG para informes
- [ ] Firma electrónica
- [ ] Panel de Super Administrador
- [ ] 2FA para médicos
- [ ] Anonimización automática de documentos
- [ ] Tests con coverage >80%

---

*Documento generado para el proyecto SecondOpinionMed - Sistema de Segunda Opinión Médica*
