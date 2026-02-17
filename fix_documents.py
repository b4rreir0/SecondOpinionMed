#!/usr/bin/env python
"""
Script para vincular documentos existentes a casos en la base de datos
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

import os
from django.conf import settings

# Buscar carpetas de casos en media/cases
cases_dir = os.path.join(settings.MEDIA_ROOT, 'cases')
print(f"Buscando en: {cases_dir}")

if os.path.exists(cases_dir):
    for case_folder in os.listdir(cases_dir):
        case_path = os.path.join(cases_dir, case_folder)
        if os.path.isdir(case_path):
            # Extraer el case_id de la carpeta
            case_id = case_folder
            print(f"\n--- Caso: {case_id} ---")
            
            # Buscar la carpeta documents
            docs_path = os.path.join(case_path, 'documents')
            if os.path.exists(docs_path):
                print(f"  Documents folder found")
                
                # Importar modelos
                from cases.models import Case, CaseDocument
                
                # Buscar el caso
                try:
                    case = Case.objects.get(case_id=case_id)
                    print(f"  Case found in DB: {case.id}")
                    
                    # Procesar cada archivo
                    for filename in os.listdir(docs_path):
                        file_path = os.path.join(docs_path, filename)
                        if os.path.isfile(file_path):
                            # Verificar si ya existe un documento
                            relative_path = os.path.join('cases', case_id, 'documents', filename)
                            existing = CaseDocument.objects.filter(case=case, file=relative_path).first()
                            
                            if not existing:
                                # Determinar el tipo de documento
                                ext = os.path.splitext(filename)[1].lower()
                                
                                if 'cv' in filename.lower() or 'curriculum' in filename.lower():
                                    doc_type = 'medical_history'
                                elif 'diagnostico' in filename.lower() or 'informe' in filename.lower():
                                    doc_type = 'diagnostic_report'
                                elif 'imagen' in filename.lower() or ext in ['.png', '.jpg', '.jpeg']:
                                    doc_type = 'imaging'
                                elif 'lab' in filename.lower() or 'resultado' in filename.lower():
                                    doc_type = 'lab_results'
                                elif 'biopsia' in filename.lower():
                                    doc_type = 'biopsy_report'
                                else:
                                    doc_type = 'other'
                                
                                # Crear el documento
                                doc = CaseDocument(
                                    case=case,
                                    file=relative_path,
                                    document_type=doc_type,
                                    description=f"Documento cargado: {filename}"
                                )
                                doc.save()
                                print(f"    + Created: {filename} ({doc_type})")
                            else:
                                print(f"    = Already exists: {filename}")
                            
                except Case.DoesNotExist:
                    print(f"  Case NOT found in DB!")
            else:
                print(f"  No documents folder")
else:
    print("Cases directory not found!")
