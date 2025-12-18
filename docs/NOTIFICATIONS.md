Notifications subsystem
======================

Overview
--------
This project includes a `notifications` Django app that provides:

- `EmailLog`, `EmailTemplate`, `DoctorInvitation`, `PatientVerification` models
- `EmailService` to create logs and queue emails
- `send_email_task` Celery task to perform sending with retry/backoff

Setup
-----

1. Add broker (Redis recommended) and set env var `CELERY_BROKER_URL`.
2. Run migrations for the new `notifications` app:

```bash
python manage.py makemigrations notifications
python manage.py migrate
```

3. Start Celery worker from project root:

```bash
celery -A oncosegunda worker -l info
```

Usage
-----

Queue an email from Python code:

```python
from notifications.services import EmailService
EmailService.create_and_queue_email('user@example.com', 'doctor_invite', context={'token': token})
```

To invite a doctor:

```python
EmailService.invite_doctor('doc@example.com', invited_by_user)
```

Notes
-----

- Ensure `DEFAULT_FROM_EMAIL` is set in environment or settings.
- Templates referenced by `EmailTemplate.template_path` should exist under `templates/` (e.g. `templates/emails/doctor_invite.html` and `templates/emails/doctor_invite.txt`).
- For production, configure secure broker and enable TLS for SMTP via environment variables.

Development notes (no Redis/Docker)
----------------------------------

- If you do not want to run Redis locally, enable eager task execution to run Celery tasks synchronously in the Django process (development only). The project already sets:

	- `CELERY_TASK_ALWAYS_EAGER = True` and `CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = True` when `DEBUG=True`.

	This makes `send_email_task.delay(...)` execute immediately and is the easiest way to test sending and `EmailLog` updates without a broker.

- Alternative: use the in-memory broker and run worker with the `solo` pool to avoid multiprocessing semaphore issues on Windows:

```powershell
# optional: set broker env for this session
$env:CELERY_BROKER_URL = 'memory://'
celery -A oncosegunda worker -l info -P solo --concurrency=1
```

	Note: `memory://` broker works only within the process and is not persistent.

