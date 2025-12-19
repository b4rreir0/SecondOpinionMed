import os,sys,shutil
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','oncosegunda.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

EMAIL = 'germanbarreiro2121@gmail.com'
EXPORT_DIR = BASE_DIR / 'exports' / EMAIL
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No se encontró usuario con email', EMAIL)
    sys.exit(1)

from cases.models import CaseDocument

qs = CaseDocument.objects.filter(case__patient=user)
if not qs.exists():
    print('No se encontraron documentos para el usuario', EMAIL)
    sys.exit(0)

exported = []
for doc in qs:
    try:
        if not doc.file:
            print('Documento sin archivo:', doc.file_name)
            continue
        src = Path(doc.file.path)
        if not src.exists():
            print('Archivo no existe en storage:', src)
            continue
        dst = EXPORT_DIR / f"{doc.case.case_id}__{doc.pk}__{doc.file_name}"
        shutil.copy2(src, dst)
        exported.append(dst)
        print('Exportado:', dst)
    except Exception as e:
        print('Error exportando', doc.pk, e)

print('\nResumen:')
print(f'Total documentos exportados: {len(exported)}')
for p in exported:
    print(p)
