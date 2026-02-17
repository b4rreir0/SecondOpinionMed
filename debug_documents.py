#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from cases.models import Case, CaseDocument

case_id = 'CASO-4B9D246B0E09'
c = Case.objects.get(case_id=case_id)
print(f'Caso: {c.case_id}')
print(f'Documentos (CaseDocument): {c.documents.count()}')

for d in c.documents.all():
    print(f'  - {d.file.name}')
    print(f'    Tipo: {d.file_type}')
    print(f'    Nombre: {d.file_name}')

# Also check if there's another relation
print('\n--- Verificando otras relaciones ---')
print(f'Has case_docs: {hasattr(c, "case_docs")}')
if hasattr(c, 'case_docs'):
    print(f'case_docs: {c.case_docs.count()}')
