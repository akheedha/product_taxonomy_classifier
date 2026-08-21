"""
Management command to run or resume a batch classification job via CLI.
"""

from django.core.management.base import BaseCommand, CommandError
from processing.services import ProcessingService
from processing.models import ClassificationJob


class Command(BaseCommand):
    help = "Run or resume a batch product classification job."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help="Maximum number of products to process (0 = all products)"
        )
        parser.add_argument(
            '--resume',
            type=int,
            default=0,
            help="ID of an existing incomplete ClassificationJob to resume"
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            default=True,
            help="Run synchronously in the current process (default: True)"
        )

    def handle(self, *args, **options):
        resume_id = options['resume']
        limit = options['limit']

        if resume_id > 0:
            self.stdout.write(self.style.MIGRATE_HEADING(f"=== Resuming Classification Job #{resume_id} ==="))
            job = ProcessingService.resume_job(job_id=resume_id, sync=True)
            if not job:
                raise CommandError(f"Job #{resume_id} not found.")
        else:
            self.stdout.write(self.style.MIGRATE_HEADING("=== Starting New Classification Job ==="))
            job = ProcessingService.create_and_dispatch_job(
                limit=limit if limit > 0 else None,
                sync=True
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nJob #{job.id} completed with status: {job.status}. "
            f"Processed: {job.processed_count}/{job.total_products} items, "
            f"Failed: {job.failed_count} items."
        ))
