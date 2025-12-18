import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from notifications.services import EmailService

User = get_user_model()

email = 'grm4nb4rreir0@gmail.com'

inviter = User.objects.filter(is_superuser=True).first()
if not inviter:
    inviter = User.objects.first()

invite = EmailService.invite_doctor(email, inviter)
print('Created invite:', invite.invited_email, 'token=', invite.token)
