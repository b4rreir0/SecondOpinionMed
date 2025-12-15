# Oncosegunda - Sistema de Segunda Opinión Oncológica

[![Django Version](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com/)
[![Python Version](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com/)

Un sistema web completo para la gestión de solicitudes de segunda opinión oncológica, desarrollado con Django y diseñado para facilitar la comunicación entre pacientes, médicos especialistas y comités multidisciplinarios.

## 🚀 Características Principales

### 👥 Gestión de Usuarios
- **Pacientes**: Registro y seguimiento de solicitudes de segunda opinión
- **Médicos**: Gestión de casos asignados y elaboración de informes
- **Administradores**: Control total del sistema y configuración

### 📋 Funcionalidades del Sistema
- **Solicitudes de Segunda Opinión**: Creación y seguimiento completo de casos
- **Asignación Automática**: Algoritmo round-robin para distribución equitativa de casos
- **Informes Médicos**: Elaboración estructurada de diagnósticos y recomendaciones
- **Comités Multidisciplinarios**: Colaboración entre especialistas
- **Documentos Adjuntos**: Gestión segura de archivos médicos
- **Auditoría Completa**: Registro de todas las acciones del sistema

### 🔒 Seguridad y Cumplimiento
- Autenticación robusta con roles y permisos
- Encriptación de datos sensibles
- Cumplimiento con regulaciones de salud
- Logs de auditoría detallados

## 🏗️ Arquitectura del Sistema

### Aplicaciones Django
```
oncosegunda/
├── core/              # Modelos base, servicios y utilidades compartidas
├── public/            # Páginas públicas y autenticación
├── pacientes/         # Gestión de pacientes y solicitudes
├── medicos/           # Gestión médica y elaboración de informes
├── administracion/    # Panel de administración del sistema
└── tests/             # Suite completa de pruebas
```

### Tecnologías Utilizadas
- **Backend**: Django 5.0 con Python 3.11
- **Base de Datos**: PostgreSQL 15
- **Cache**: Redis 7
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Despliegue**: Docker & Docker Compose
- **Servidor Web**: Nginx + Gunicorn
- **Testing**: pytest con Factory Boy

## 📋 Prerrequisitos

- Docker y Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (opcional, para desarrollo frontend)

## 🚀 Instalación y Despliegue

### Opción 1: Despliegue con Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/oncosegunda.git
   cd oncosegunda
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Desplegar con Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Ejecutar migraciones**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Crear superusuario**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Opción 2: Instalación Local (Desarrollo)

1. **Clonar y configurar entorno virtual**
   ```bash
   git clone https://github.com/tu-usuario/oncosegunda.git
   cd oncosegunda
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar base de datos**
   ```bash
   # Crear base de datos PostgreSQL
   createdb oncosegunda_dev
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env para desarrollo local
   ```

5. **Ejecutar migraciones y servidor**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DJANGO_SECRET_KEY` | Clave secreta de Django | *Requerido* |
| `DB_NAME` | Nombre de la base de datos | `oncosegunda_prod` |
| `DB_USER` | Usuario de la base de datos | `oncosegunda_user` |
| `DB_PASSWORD` | Contraseña de la base de datos | *Requerido* |
| `REDIS_URL` | URL de conexión a Redis | `redis://127.0.0.1:6379/1` |
| `EMAIL_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `EMAIL_HOST_USER` | Usuario del email | *Requerido para envío* |
| `EMAIL_HOST_PASSWORD` | Contraseña del email | *Requerido para envío* |

### Configuración de Producción

Para despliegue en producción:

1. **Configurar SSL/HTTPS**
   ```bash
   docker-compose --profile nginx up -d
   ```

2. **Configurar certificados SSL con Let's Encrypt**
   ```bash
   docker-compose --profile certbot run --rm certbot
   ```

3. **Monitoreo de salud**
   - Endpoint: `https://tu-dominio/health/`
   - Logs: `/var/log/oncosegunda/`

## 🧪 Testing

### Ejecutar Tests
```bash
# Con Docker
docker-compose exec web python manage.py test

# Local
python manage.py test
```

### Cobertura de Tests
```bash
# Instalar pytest-cov
pip install pytest-cov

# Ejecutar con cobertura
pytest --cov=. --cov-report=html
```

## 📚 Documentación de API

### Endpoints Principales

#### Autenticación
- `POST /api/auth/login/` - Inicio de sesión
- `POST /api/auth/logout/` - Cierre de sesión
- `POST /api/auth/register/` - Registro de usuario

#### Pacientes
- `GET /api/pacientes/solicitudes/` - Listar solicitudes
- `POST /api/pacientes/solicitudes/` - Crear solicitud
- `GET /api/pacientes/solicitudes/{id}/` - Detalle de solicitud

#### Médicos
- `GET /api/medicos/casos/` - Listar casos asignados
- `POST /api/medicos/casos/{id}/informe/` - Crear informe
- `PUT /api/medicos/casos/{id}/estado/` - Actualizar estado

#### Administración
- `GET /api/admin/usuarios/` - Gestión de usuarios
- `GET /api/admin/configuracion/` - Configuración del sistema
- `GET /api/admin/estadisticas/` - Estadísticas del sistema

## 🔍 Monitoreo y Logs

### Logs del Sistema
- **Aplicación**: `/var/log/oncosegunda/django.log`
- **Nginx**: `/var/log/nginx/`
- **PostgreSQL**: `/var/log/postgresql/`

### Métricas de Salud
- **Endpoint**: `/health/`
- **Base de datos**: Conectividad y rendimiento
- **Cache**: Estado de Redis
- **Almacenamiento**: Uso de disco

## 🚀 Despliegue en Producción

### Con Docker Compose
```bash
# Producción completa
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Con Nginx y SSL
docker-compose --profile nginx --profile certbot up -d
```

### Con Kubernetes (Avanzado)
```bash
# Aplicar manifests
kubectl apply -f k8s/
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código
- **Python**: PEP 8 con Black
- **JavaScript**: ESLint
- **Commits**: Conventional Commits
- **Tests**: Cobertura mínima del 80%

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/oncosegunda/issues)
- **Email**: soporte@oncosegunda.com
- **Documentación**: [Wiki](https://github.com/tu-usuario/oncosegunda/wiki)

## 🙏 Agradecimientos

- Comunidad Django por el excelente framework
- Contribuidores y testers beta
- Instituciones médicas colaboradoras

---

**Desarrollado con ❤️ para mejorar la atención oncológica**