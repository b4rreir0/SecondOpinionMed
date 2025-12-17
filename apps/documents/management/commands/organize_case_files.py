from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from cases.models import CaseDocument, Case
import os
import shutil
import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = 'Organiza archivos de casos agrupándolos por case_id en S3 o en local MEDIA_ROOT. Usa --dry-run para simular.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='No realiza cambios; muestra lo que haría')
        parser.add_argument('--s3', action='store_true', help='Operar sobre S3 (por defecto opera sobre MEDIA_ROOT si existe)')
        parser.add_argument('--delete-old', action='store_true', help='Eliminar objetos/archivos antiguos después de copiar (use con precaución)')
        parser.add_argument('--confirm', action='store_true', help='Confirmación necesaria para borrar cuando se usa --delete-old')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        use_s3 = options['s3']
        delete_old = options['delete_old']
        confirm = options['confirm']

        if delete_old and not confirm:
            raise CommandError('Para borrar archivos antiguas con --delete-old debe pasar también --confirm')

        docs = CaseDocument.objects.select_related('case').all()
        if not docs.exists():
            self.stdout.write('No se encontraron CaseDocument en la base de datos.')
            return

        if use_s3:
            bucket = getattr(settings, 'AWS_S3_BUCKET_NAME', None)
            if not bucket:
                raise CommandError('No está configurado AWS_S3_BUCKET_NAME en settings')
            s3 = boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name=getattr(settings, 'AWS_REGION', None),
            )

        moved = 0
        errors = 0

        for cd in docs:
            try:
                case = cd.case
                if not case or not case.case_id:
                    self.stdout.write(self.style.WARNING(f'CaseDocument id={cd.id} no tiene case relacionado; se omite'))
                    continue

                desired_prefix = f"cases/{case.case_id}/"
                current_key = cd.s3_file_path or ''

                if use_s3 and current_key:
                    # If already under desired prefix, skip
                    if current_key.startswith(desired_prefix):
                        continue

                    filename = os.path.basename(current_key)
                    new_key = f"{desired_prefix}{filename}"

                    self.stdout.write(f"S3: Caso {case.case_id} - mover {current_key} -> {new_key}")
                    if not dry_run:
                        # Copy object
                        s3.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': current_key}, Key=new_key)
                        # Update DB
                        cd.s3_file_path = new_key
                        cd.save()
                        if delete_old:
                            try:
                                s3.delete_object(Bucket=bucket, Key=current_key)
                            except ClientError as e:
                                self.stderr.write(f'Error borrando objeto {current_key}: {e}')
                        moved += 1

                else:
                    # Operar sobre filesystem: MEDIA_ROOT
                    media_root = getattr(settings, 'MEDIA_ROOT', None)
                    if not media_root:
                        self.stderr.write('MEDIA_ROOT no configurado; use --s3 para operar en S3')
                        errors += 1
                        continue

                    # Try interpret s3_file_path as a relative path under media_root or file_name
                    candidate = cd.s3_file_path or cd.file_name or ''
                    if not candidate:
                        self.stdout.write(self.style.WARNING(f'CaseDocument id={cd.id} no tiene ruta/archivo asociado; se omite'))
                        continue

                    # Normalize path
                    src_path = os.path.join(media_root, candidate) if not os.path.isabs(candidate) else candidate
                    if not os.path.exists(src_path):
                        # Maybe file is directly in media_root under file_name
                        alt = os.path.join(media_root, cd.file_name)
                        if os.path.exists(alt):
                            src_path = alt
                        else:
                            self.stderr.write(f'Archivo no encontrado en disco: {src_path} (CaseDocument id={cd.id})')
                            errors += 1
                            continue

                    dest_dir = os.path.join(media_root, 'cases', str(case.case_id))
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, os.path.basename(src_path))

                    self.stdout.write(f'FS: Caso {case.case_id} - mover {src_path} -> {dest_path}')
                    if not dry_run:
                        shutil.copy2(src_path, dest_path)
                        cd.s3_file_path = os.path.relpath(dest_path, media_root)
                        cd.save()
                        if delete_old:
                            try:
                                os.remove(src_path)
                            except Exception as e:
                                self.stderr.write(f'Error borrando archivo {src_path}: {e}')
                        moved += 1

            except Exception as e:
                errors += 1
                self.stderr.write(f'Error procesando CaseDocument id={getattr(cd, "id", "?")}: {e}')

        self.stdout.write(self.style.SUCCESS(f'Proceso finalizado. Moved={moved} Errors={errors}'))
