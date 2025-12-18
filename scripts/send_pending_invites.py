import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from notifications.models import DoctorInvitation
from notifications.services import EmailService
from django.utils import timezone

pending = DoctorInvitation.objects.filter(is_used=False, expires_at__gte=timezone.now())
print(f'Found {pending.count()} pending invites')
for inv in pending:
    print('Enqueuing:', inv.invited_email, inv.token)
    EmailService.create_and_queue_email(
        recipient=inv.invited_email,
        template_name='doctor_invite',
        context={'token': str(inv.token), 'invited_by': inv.invited_by.get_full_name() if inv.invited_by else '', 'register_url': getattr(__import__('django.conf').conf.settings, 'SITE_ROOT', '') + f"/accounts/register/{inv.token}/"},
        subject='Invitación para unirse como médico'
    )

print('Done')
