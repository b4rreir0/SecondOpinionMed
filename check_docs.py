import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from apps.cases.models import CaseDocument

docs = CaseDocument.objects.all()
print(f'Total docs: {docs.count()}')
print()
for d in docs:
    print(f'Doc {d.id}: case={d.case.case_id}, file={d.file}, file_name={d.file_name}, file_exists={d.file and d.file.name}')