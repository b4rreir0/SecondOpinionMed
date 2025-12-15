# Sistema de Segunda Opinión Oncológica

Una plataforma web completa para la gestión de solicitudes de segunda opinión oncológica, construida con Django.

## Características Principales

- **Gestión de Usuarios**: Sistema de roles (Pacientes, Médicos, Administradores)
- **Solicitudes de Segunda Opinión**: Proceso completo desde solicitud hasta informe final
- **Asignación Automática**: Algoritmo round-robin para asignar casos a médicos
- **Comités Multidisciplinarios**: Sistema de revisión por comités especializados
- **Auditoría Completa**: Registro de todas las acciones del sistema
- **Interfaz Moderna**: Bootstrap 5 con diseño responsive
- **API REST**: Endpoints para integración con otros sistemas
- **Docker**: Despliegue containerizado para desarrollo y producción

## Tecnologías

- **Backend**: Django 6.0, Python 3.11
- **Base de Datos**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Cache**: Redis
- **Servidor Web**: Nginx + Gunicorn
- **Contenedor**: Docker & Docker Compose

## Instalación y Configuración

### Prerrequisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- PostgreSQL (opcional para desarrollo local)

### Instalación con Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd oncosegunda
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con sus configuraciones
   ```

3. **Levantar servicios**
   ```bash
   # Para desarrollo
   docker-compose -f docker-compose.dev.yml up --build

   # Para producción
   docker-compose up --build
   ```

4. **Crear datos iniciales**
   ```bash
   docker-compose exec web python manage.py create_initial_data
   ```

### Instalación Local (Desarrollo)

1. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate     # Windows
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. **Configurar base de datos**
   ```bash
   createdb oncosegunda_dev
   python manage.py migrate
   python manage.py create_initial_data
   ```

4. **Ejecutar servidor**
   ```bash
   python manage.py runserver
   ```

## Estructura del Proyecto

```
oncosegunda/
├── core/                    # Utilidades compartidas
│   ├── models.py           # Modelos base y auditoría
│   ├── services.py         # Servicios de negocio
│   ├── decorators.py       # Decoradores de acceso
│   ├── middleware.py       # Middleware personalizado
│   └── context_processors.py
├── public/                 # Módulo público
│   ├── views.py           # Landing, login, registro
│   ├── forms.py           # Formularios públicos
│   └── templates/public/
├── pacientes/             # Módulo pacientes
│   ├── models.py          # Modelo Paciente
│   ├── views.py           # Dashboard y solicitudes
│   ├── forms.py           # Formularios pacientes
│   └── templates/pacientes/
├── medicos/               # Módulo médicos
│   ├── models.py          # Modelo Medico
│   ├── views.py           # Gestión de casos
│   ├── forms.py           # Formularios médicos
│   └── templates/medicos/
├── administracion/        # Módulo administración
│   ├── models.py          # Configuración sistema
│   ├── views.py           # Panel admin
│   └── templates/administracion/
├── static/                # Archivos estáticos
├── media/                 # Archivos subidos
├── templates/             # Templates base
└── tests/                 # Tests unitarios
```

## Configuración

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# Django
DJANGO_SETTINGS_MODULE=oncosegunda.settings_prod
DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here

# Base de datos
DB_NAME=oncosegunda_prod
DB_USER=oncosegunda_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (opcional)
USE_S3=False
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

## Uso del Sistema

### Roles de Usuario

1. **Paciente**
   - Registro y perfil
   - Crear solicitudes de segunda opinión
   - Subir documentos médicos
   - Seguimiento de casos

2. **Médico**
   - Revisar casos asignados
   - Validar documentación
   - Generar informes
   - Participar en comités

3. **Administrador**
   - Gestión de usuarios
   - Configuración del sistema
   - Monitoreo y reportes
   - Gestión de módulos

### Flujo de Trabajo

1. **Paciente** crea solicitud con documentos
2. Sistema **asigna automáticamente** caso a médico disponible
3. **Médico** valida documentación y genera informe preliminar
4. Sistema puede **escalar** a comité multidisciplinario si es necesario
5. **Comité** revisa caso y genera informe final
6. **Paciente** recibe notificación con resultados

## Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_models.py
pytest tests/test_services.py -v
```

## Despliegue en Producción

### Con Docker Compose

```bash
# Construir y desplegar
docker-compose up --build -d

# Ver logs
docker-compose logs -f web

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Recolectar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

### Configuración SSL con Let's Encrypt

```bash
# Obtener certificado
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot --email your-email@example.com -d yourdomain.com

# Renovar certificados
docker-compose run --rm certbot renew
```

## API REST

El sistema incluye una API REST para integración con otros sistemas médicos.

### Endpoints principales

- `GET /api/pacientes/` - Lista de pacientes
- `POST /api/solicitudes/` - Crear solicitud
- `GET /api/medicos/casos/` - Casos asignados
- `POST /api/informes/` - Crear informe

Documentación completa disponible en `/api/docs/` cuando el sistema está ejecutándose.

## Monitoreo y Logs

### Logs del Sistema

- **Aplicación**: `/var/log/oncosegunda/django.log`
- **Nginx**: `/var/log/nginx/`
- **PostgreSQL**: Configurado en docker logs

### Métricas

- Health check: `GET /health/`
- Métricas de aplicación disponibles en el panel de administración

## Seguridad

- Autenticación basada en roles
- Encriptación de contraseñas
- Validación de archivos subidos
- Protección CSRF
- Headers de seguridad HTTP
- Rate limiting
- Auditoría completa de acciones

## Reglas de Negocio

### 1. Rol del Responsable del Caso
- **Función Primaria:** Redactor final oficial de la institución.
- **Responsabilidad:** Sintetizar el consenso del Comité Multidisciplinario (MDT) en un informe formal dirigido al paciente, emitido "En nombre de la Institución".

### 2. Algoritmo de Asignación Automática y Equitativa (Rotativa)
- **Regla Base:** Basada en la especialidad oncológica requerida.
- **Mecanismo de Rotación (Round Robin):**
  - Lista ordenada de responsables por especialidad.
  - Asignación secuencial, reinicio al completar la lista.
  - Objetivo: Distribución equitativa de carga.

### 3. Protocolo de Comunicación con el Paciente
- **Contacto Telefónico:** Número de teléfono prominente como "Dato Crítico".
- **Iniciativa:** Solo por miembros del MDT analizando el caso.
- **Registro:** Toda llamada debe registrarse con fecha, hora, médico y resumen.

## Diagrama de Flujo del Algoritmo de Asignación

```mermaid
flowchart TD
    A[Caso Nuevo Ingresa<br>Especialidad: Pulmón] --> B{¿Hay responsables<br>para esta especialidad?}

    B -- Sí --> C[Obtener lista ordenada<br>de responsables de Pulmón]
    C --> D{Verificar estado de carga<br>del próximo en la lista}

    D -- Disponible --> E[Asignar caso al responsable]
    E --> F[Rotar lista:<br>Mover responsable al final]
    F --> G[Asignación Completada]

    D -- No Disponible<br>Ej. Vacaciones --> H[Marcar como temporalmente<br>no disponible]
    H --> I[Buscar siguiente<br>responsable en lista]
    I --> D

    B -- No --> J[Estado: "Pendiente de Asignación<br>Especialista"<br>Notificar a Coordinación]
```

## Tabla de Estados del Sistema

| Estado del Sistema | ¿Quién lo Cambia? | Significado y Acciones Permitidas |
|--------------------|-------------------|-----------------------------------|
| Pendiente de Asignación | Sistema (automático) | Caso en cola esperando responsable disponible. |
| Asignado a [Dr. X] | Sistema (automático) | Responsable revisa documentación, puede solicitar info o enviar a MDT. |
| Esperando Info del Paciente | Responsable del Caso | Contacto al paciente para documentos faltantes. |
| En Análisis por MDT | Responsable del Caso | Discusión activa. Habilita "Contactar al Paciente" para miembros MDT. |
| Informe en Redacción | Responsable del Caso | Decisión tomada, redacción del informe institucional. |
| Concluido – Informe Enviado | Sistema (automático) | Informe enviado, caso archivado. |

## Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas:
- Email: soporte@oncosegunda.com
- Documentación: [Wiki del proyecto]
- Issues: [GitHub Issues]

## Roadmap

- [ ] API GraphQL
- [ ] Aplicación móvil
- [ ] Integración con HIS (Sistemas de Información Hospitalaria)
- [ ] IA para análisis preliminar de casos
- [ ] Telemedicina integrada
- [ ] Reportes avanzados y analytics

**Nota:** La función "llamar al paciente" solo visible en estado "En Análisis por MDT" para roles "Miembro MDT" o "Responsable".