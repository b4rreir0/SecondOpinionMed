import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from notifications.models import EmailLog

logs = EmailLog.objects.all().order_by('-created_at')[:50]
if not logs:
    print('No email logs found')
    sys.exit(0)

for e in logs:
    print('---')
    print('id:', e.id)
    print('recipient:', e.recipient)
    print('subject:', e.subject)
    print('template_name:', e.template_name)
    print('status:', e.status)
    print('retries:', e.retries_attempted)
    print('sent_at:', e.sent_at)
    print('error_message:', e.error_message)
    print('created_at:', e.created_at)
    print('context:', e.context_json)

# Optional: attempt to resend failed/pending ones synchronously
resend = os.getenv('RESEND', '0')
if resend == '1':
    from notifications.tasks import send_email_task
    for e in logs:
        if e.status in [EmailLog.STATUS_PENDING, EmailLog.STATUS_FAILED, EmailLog.STATUS_RETRYING]:
            print(f"Attempting send for EmailLog {e.id} -> {e.recipient}")
            send_email_task.apply(args=(e.id,))
            updated = EmailLog.objects.get(id=e.id)
            print('new status:', updated.status, 'sent_at:', updated.sent_at, 'error:', updated.error_message)

print('\nDone')
