"""
Management command to import catalog products via CLI using ImportService.
"""

from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from imports.services import ImportService


class Command(BaseCommand):
    help = "Import catalog products from an .xlsx, .xls, or .csv spreadsheet file."

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            nargs='?',
            type=str,
            help="Path to the Excel (.xlsx/.xls) or CSV spreadsheet file to import."
        )
        parser.add_argument(
            '--file',
            type=str,
            dest='file_opt',
            help="Alternative flag to specify spreadsheet file path."
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default='0',
            help="Sheet name or index to read from Excel file (default: 0)"
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help="Batch size for database bulk operations (default: 1000)"
        )

    def handle(self, *args, **options):
        file_path_str = options['file_opt'] or options['file_path']
        if not file_path_str:
            raise CommandError("Please provide a file path: python manage.py import_products <path_to_file.xlsx>")

        file_path = Path(file_path_str).resolve()
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        sheet_raw = options['sheet']
        sheet = int(sheet_raw) if sheet_raw.isdigit() else sheet_raw

        self.stdout.write(self.style.MIGRATE_HEADING(f"=== Ingesting Catalog: {file_path.name} ==="))

        try:
            res = ImportService.import_catalog_file(
                file_path=str(file_path),
                sheet=sheet,
                batch_size=options['batch_size'],
            )

            self.stdout.write(self.style.SUCCESS(
                f"\nSuccessfully imported {res['imported_count']:,} of {res['total_rows']:,} rows in {res['elapsed_seconds']}s."
            ))
            self.stdout.write(f"Skipped empty rows: {res['skipped_count']}")
            metrics = res.get('data_quality_metrics', {})
            self.stdout.write(f"Missing descriptions: {metrics.get('missing_description_count', 0)}")
            self.stdout.write(f"Missing images: {metrics.get('missing_images_count', 0)}")

        except Exception as exc:
            raise CommandError(f"Import failed: {exc}")
