"""
Management command to create and run product taxonomy classification jobs.
Dispatches asynchronous Celery task or executes synchronously.
"""

import time
from typing import Any, List
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from catalog.models import Product
from classification.models import ClassificationJob, ClassificationResult
from classification.tasks import process_classification_job


class Command(BaseCommand):
    help = "Creates a ClassificationJob for unclassified products and dispatches the classification pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help="Maximum number of products to classify (e.g. --limit 50 for testing)."
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help="Force re-classification for all products even if already classified."
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help="Run the job synchronously in the foreground instead of dispatching to Celery worker."
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force_all = options['all']
        run_sync = options['sync']

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Initiating Classification Job ==="))

        # 1. Query candidate products
        if force_all:
            queryset = Product.objects.all().order_by('id')
        else:
            # Query products that don't have a 'done' ClassificationResult
            done_product_ids = ClassificationResult.objects.filter(
                status=ClassificationResult.Status.DONE
            ).values_list('product_id', flat=True)
            queryset = Product.objects.exclude(id__in=done_product_ids).order_by('id')

        if limit:
            products = list(queryset[:limit])
        else:
            products = list(queryset)

        if not products:
            self.stdout.write(
                self.style.WARNING("No unclassified products found in catalog. Use --all to re-classify existing products.")
            )
            return

        total_count = len(products)
        self.stdout.write(f"Queuing {total_count} products for taxonomy classification...")

        # 2. Create ClassificationJob
        job = ClassificationJob.objects.create(
            status=ClassificationJob.Status.PENDING,
            total_products=total_count,
            processed_count=0,
            failed_count=0,
        )

        # 3. Pre-create ClassificationResult stubs
        result_stubs = [
            ClassificationResult(
                product=product,
                job=job,
                status=ClassificationResult.Status.PENDING
            )
            for product in products
        ]
        ClassificationResult.objects.bulk_create(result_stubs, batch_size=500)

        self.stdout.write(
            self.style.SUCCESS(f"Created ClassificationJob #{job.id} with {total_count} pending results.")
        )

        # 4. Dispatch Celery Task or Run Synchronously
        if run_sync:
            self.stdout.write("Running classification job synchronously...")
            start_t = time.time()
            res = process_classification_job(job.id)
            duration = time.time() - start_t
            self.stdout.write(f"Job completed synchronously in {duration:.2f}s.")
            self._print_job_summary(job.id)
        else:
            try:
                task_result = process_classification_job.delay(job.id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Dispatched Celery task [{task_result.id}] for Job #{job.id}.\n"
                        f"Check worker logs or inspect progress in Django admin."
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Could not connect to Celery/Redis broker ({e}).\n"
                        f"Falling back to synchronous execution..."
                    )
                )
                start_t = time.time()
                process_classification_job(job.id)
                duration = time.time() - start_t
                self.stdout.write(f"Job completed in {duration:.2f}s.")
                self._print_job_summary(job.id)

    def _print_job_summary(self, job_id: int):
        """Print formatted analytics summary for the completed job."""
        job = ClassificationJob.objects.get(id=job_id)
        results = ClassificationResult.objects.filter(job=job).select_related('predicted_category', 'product')

        done_count = results.filter(status=ClassificationResult.Status.DONE).count()
        failed_count = results.filter(status=ClassificationResult.Status.FAILED).count()
        review_count = results.filter(needs_manual_review=True).count()
        high_conf_count = results.filter(confidence__gte=0.70).count()

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== Classification Job #{job.id} Summary ==="))
        self.stdout.write(f"  - Total Products:        {job.total_products}")
        self.stdout.write(f"  - Successfully Done:     {done_count} ({(done_count/job.total_products)*100:.1f}%)")
        self.stdout.write(f"  - Failed:                {failed_count}")
        self.stdout.write(f"  - Needs Manual Review:   {review_count} ({(review_count/job.total_products)*100:.1f}%)")
        self.stdout.write(f"  - High Confidence (>=70%): {high_conf_count} ({(high_conf_count/job.total_products)*100:.1f}%)")
        if job.duration_seconds:
            self.stdout.write(f"  - Execution Duration:    {job.duration_seconds:.2f} seconds")

        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Sample Classification Results (First 5) ---"))
        for res in results.filter(status=ClassificationResult.Status.DONE)[:5]:
            cat_name = res.predicted_category.full_name if res.predicted_category else "N/A"
            flag = "[REVIEW]" if res.needs_manual_review else "[OK]"
            self.stdout.write(
                f"  [{flag}] SKU: {res.product.product_number} | {res.product.product_name[:35]}"
            )
            self.stdout.write(f"         Category:   {cat_name}")
            self.stdout.write(f"         Confidence: {res.confidence:.4f} ({res.confidence*100:.1f}%)")
            if res.extracted_attributes:
                attrs_str = ", ".join([f"{k}='{v['value']}'" for k, v in res.extracted_attributes.items()])
                self.stdout.write(f"         Attributes: {attrs_str}")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Job execution completed!"))
