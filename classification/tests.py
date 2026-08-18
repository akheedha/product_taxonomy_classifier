from unittest.mock import patch
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product
from taxonomy.models import Attribute, AttributeValue, Category
from classification.models import ClassificationJob, ClassificationResult
from classification.engine.text_classifier import TextCategoryClassifier, classify_text
from classification.engine.image_classifier import classify_image, download_image
from classification.engine.attribute_extractor import extract_attributes
from classification.engine.fusion import (
    classify_product,
    TEXT_WEIGHT,
    IMAGE_WEIGHT,
    CONFIDENCE_THRESHOLD,
    AMBIGUITY_GAP_THRESHOLD,
)
from classification.tasks import process_classification_job


class ClassificationModelTests(TestCase):
    def setUp(self):
        # Create Category
        self.category = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/aa-1",
            name="Clothing",
            full_name="Apparel & Accessories > Clothing",
            level=1
        )
        self.alt_category = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/aa-2",
            name="Shoes",
            full_name="Apparel & Accessories > Shoes",
            level=1
        )

        # Create Product
        self.product = Product.objects.create(
            product_number="SKU-TEST-500",
            product_name="Casual Cotton T-Shirt",
            product_category="Apparel"
        )

        # Create Classification Job
        self.job = ClassificationJob.objects.create(
            status=ClassificationJob.Status.RUNNING,
            total_products=10,
            processed_count=5,
            failed_count=0
        )

    def test_job_progress_and_string(self):
        self.assertEqual(self.job.progress_percentage, 50.0)
        self.assertIn("Job #", str(self.job))
        self.assertIn("Running", str(self.job))

    def test_create_classification_result(self):
        result = ClassificationResult.objects.create(
            product=self.product,
            job=self.job,
            predicted_category=self.category,
            confidence=0.92,
            alternative_categories=[
                {"category_id": self.alt_category.id, "name": self.alt_category.name, "score": 0.08}
            ],
            extracted_attributes={
                "Color": {"value": "Navy Blue", "confidence": 0.95},
                "Material": {"value": "100% Cotton", "confidence": 0.90}
            },
            needs_manual_review=False,
            status=ClassificationResult.Status.DONE,
            approved=True,
            reviewed_by="admin"
        )

        self.assertEqual(ClassificationResult.objects.count(), 1)
        self.assertEqual(result.product, self.product)
        self.assertEqual(result.job, self.job)
        self.assertEqual(result.predicted_category, self.category)
        self.assertEqual(result.confidence, 0.92)
        self.assertEqual(len(result.alternative_categories), 1)
        self.assertEqual(result.extracted_attributes["Color"]["value"], "Navy Blue")
        self.assertTrue(result.approved)

    def test_unique_product_job_constraint(self):
        # First result succeeds
        ClassificationResult.objects.create(
            product=self.product,
            job=self.job,
            predicted_category=self.category,
            confidence=0.85
        )

        # Second result with same (product, job) must fail integrity check
        with self.assertRaises(IntegrityError):
            ClassificationResult.objects.create(
                product=self.product,
                job=self.job,
                predicted_category=self.alt_category,
                confidence=0.70
            )

    def test_query_by_manual_review_and_status(self):
        # Result 1: Needs review
        ClassificationResult.objects.create(
            product=self.product,
            job=self.job,
            predicted_category=self.category,
            confidence=0.45,
            needs_manual_review=True,
            status=ClassificationResult.Status.DONE
        )

        # Product 2: High confidence
        product2 = Product.objects.create(
            product_number="SKU-TEST-501",
            product_name="Leather Boots"
        )
        ClassificationResult.objects.create(
            product=product2,
            job=self.job,
            predicted_category=self.alt_category,
            confidence=0.98,
            needs_manual_review=False,
            status=ClassificationResult.Status.DONE
        )

        review_queue = ClassificationResult.objects.filter(
            needs_manual_review=True,
            status=ClassificationResult.Status.DONE
        )
        self.assertEqual(review_queue.count(), 1)
        self.assertEqual(review_queue.first().product, self.product)


class TextClassifierEngineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat_sofas = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/furn-1",
            name="Sofas",
            full_name="Furniture > Sofas",
            level=1
        )
        cls.cat_chairs = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/furn-2",
            name="Armchairs",
            full_name="Furniture > Chairs > Armchairs",
            level=2
        )
        cls.cat_tables = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/furn-3",
            name="Dining Tables",
            full_name="Furniture > Tables > Dining Tables",
            level=2
        )

    def test_build_product_text_with_description(self):
        classifier = TextCategoryClassifier.get_instance(force_recompute=True)
        product = Product(
            product_number="PROD-001",
            product_name="Modern Velvet Sectional Sofa",
            product_category="Living Room",
            product_sub_category="Sofas",
            materials="Velvet, Solid Wood",
            product_description="High quality sectional sofa for large living rooms."
        )
        text, is_low_info = classifier.build_product_text(product)
        self.assertIn("Modern Velvet Sectional Sofa", text)
        self.assertIn("Velvet, Solid Wood", text)
        self.assertFalse(is_low_info)

    def test_build_product_text_missing_description(self):
        classifier = TextCategoryClassifier.get_instance()
        product = Product(
            product_number="PROD-002",
            product_name="Wooden Coffee Table",
            product_category="Furniture",
            product_description=""
        )
        text, is_low_info = classifier.build_product_text(product)
        self.assertTrue(is_low_info)

    def test_classify_text_returns_top_predictions(self):
        product = Product(
            product_number="PROD-003",
            product_name="Solid Oak Dining Table",
            product_category="Dining Room",
            product_description="Extendable oak table with seating for up to 8 people."
        )
        predictions, meta = classify_text(product, top_k=2)
        self.assertEqual(len(predictions), 2)
        self.assertEqual(predictions[0]["category_id"], self.cat_tables.id)
        self.assertGreater(predictions[0]["score"], 0.4)
        self.assertFalse(meta["is_low_info"])


class ImageClassifierEngineTests(TestCase):
    def test_classify_image_broken_url_returns_empty_safely(self):
        # Invalid / broken / unreachable URL must never raise, returns []
        candidates = [{"id": "1", "name": "Sofas", "full_name": "Furniture > Sofas"}]
        result = classify_image("https://invalid-non-existent-domain.xyz/broken.jpg", candidates, product_id="PROD-ERR")
        self.assertEqual(result, [])

    def test_classify_image_empty_url_returns_empty(self):
        result = classify_image("", [{"id": "1", "name": "Sofas"}])
        self.assertEqual(result, [])

    def test_classify_image_empty_candidates_returns_empty(self):
        result = classify_image("https://example.com/image.jpg", [])
        self.assertEqual(result, [])


class AttributeExtractorEngineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/attr-cat-1",
            name="Sofas",
            full_name="Furniture > Sofas",
            level=1
        )
        # Attribute: Material
        cls.attr_material = Attribute.objects.create(
            id="gid://shopify/TaxonomyAttribute/mat-1",
            name="Material"
        )
        cls.attr_material.categories.add(cls.category)
        AttributeValue.objects.create(
            id="gid://shopify/TaxonomyAttributeValue/mat-v1",
            attribute=cls.attr_material,
            value="Velvet"
        )
        AttributeValue.objects.create(
            id="gid://shopify/TaxonomyAttributeValue/mat-v2",
            attribute=cls.attr_material,
            value="Leather"
        )
        AttributeValue.objects.create(
            id="gid://shopify/TaxonomyAttributeValue/mat-v3",
            attribute=cls.attr_material,
            value="Solid Wood"
        )

        # Attribute: Color
        cls.attr_color = Attribute.objects.create(
            id="gid://shopify/TaxonomyAttribute/col-1",
            name="Color"
        )
        cls.attr_color.categories.add(cls.category)
        AttributeValue.objects.create(
            id="gid://shopify/TaxonomyAttributeValue/col-v1",
            attribute=cls.attr_color,
            value="Navy Blue"
        )
        AttributeValue.objects.create(
            id="gid://shopify/TaxonomyAttributeValue/col-v2",
            attribute=cls.attr_color,
            value="Emerald Green"
        )

    def test_extract_attributes_exact_and_fuzzy_matches(self):
        product = Product(
            product_number="ATTR-001",
            product_name="Luxurious Velvet Sectional Sofa",
            product_color="Navy Blue",
            materials="Velvet Fabric and Solid Wood Frame",
            product_description="Stunning handcrafted sectional in deep navy."
        )

        extracted = extract_attributes(product, self.category, similarity_threshold=80.0)

        # Check Material was extracted
        self.assertIn("Material", extracted)
        self.assertIn(extracted["Material"]["value"], ["Velvet", "Solid Wood"])
        self.assertGreaterEqual(extracted["Material"]["confidence"], 0.8)

        # Check Color was extracted
        self.assertIn("Color", extracted)
        self.assertEqual(extracted["Color"]["value"], "Navy Blue")
        self.assertGreaterEqual(extracted["Color"]["confidence"], 0.8)

    def test_extract_attributes_skips_unmatched(self):
        product = Product(
            product_number="ATTR-002",
            product_name="Plastic Outdoor Stool",
            materials="Polypropylene",
            product_color="Yellow"
        )

        extracted = extract_attributes(product, self.category, similarity_threshold=80.0)
        self.assertEqual(extracted, {})

    def test_extract_attributes_safe_on_empty(self):
        # Empty product or None category must safely return {} without raising
        self.assertEqual(extract_attributes(None, self.category), {})
        self.assertEqual(extract_attributes(Product(), None), {})


class FusionEngineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat_sofas = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/fuse-sofa-1",
            name="Chesterfield Sofas",
            full_name="Furniture > Living Room Furniture > Sofas > Chesterfield Sofas",
            level=3
        )
        cls.cat_chairs = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/fuse-chair-1",
            name="Dining Chairs",
            full_name="Furniture > Dining Room Furniture > Chairs > Dining Chairs",
            level=3
        )

    def test_classify_product_text_only(self):
        product = Product.objects.create(
            product_number="FUSE-SKU-001",
            product_name="Contemporary Velvet Chesterfield Sofa",
            product_category="Living Room",
            product_description="Plush tufted velvet chesterfield sofa."
        )

        result = classify_product(product)
        self.assertEqual(result["status"], "done")
        self.assertFalse(result["used_image"])
        self.assertIn(result["category_id"], [self.cat_sofas.id, "gid://shopify/TaxonomyCategory/task-cat-1", "gid://shopify/TaxonomyCategory/attr-cat-1", "gid://shopify/TaxonomyCategory/furn-1"])
        self.assertGreater(result["confidence"], 0.4)
        self.assertIn("extracted_attributes", result)

    def test_classify_product_with_mocked_image_fusion(self):
        product = Product.objects.create(
            product_number="FUSE-SKU-002",
            product_name="Contemporary Living Room Seating",
            product_category="Furniture",
            product_description="Comfortable modern seating item with sturdy frame.",
            images=["https://example.com/mock-chair.jpg"]
        )

        # Mock image classifier returning high score for Chairs
        mock_image_preds = [
            ({"category_id": self.cat_chairs.id, "name": self.cat_chairs.name}, 0.90),
            ({"category_id": self.cat_sofas.id, "name": self.cat_sofas.name}, 0.30),
        ]

        with patch("classification.engine.fusion.classify_image", return_value=mock_image_preds):
            result = classify_product(product)
            self.assertTrue(result["used_image"])
            self.assertIn("category_id", result)
            self.assertIsNotNone(result["confidence"])
            self.assertIn("extracted_attributes", result)

    def test_needs_manual_review_threshold_heuristics(self):
        # Low confidence forces manual review
        product = Product.objects.create(
            product_number="FUSE-SKU-003",
            product_name="Generic Ambiguous Item X",
            product_description=""
        )
        result = classify_product(product, confidence_threshold=0.99)
        self.assertTrue(result["needs_manual_review"])
        self.assertTrue(any("confidence" in r.lower() or "low information" in r.lower() for r in result["review_reasons"]))


class ClassificationTaskTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/task-cat-1",
            name="Sofas",
            full_name="Furniture > Sofas",
            level=1
        )
        self.prod1 = Product.objects.create(
            product_number="TASK-P1",
            product_name="Modern Loveseat",
            product_description="Cozy two-person sofa"
        )
        self.prod2 = Product.objects.create(
            product_number="TASK-P2",
            product_name="Sectional Couch",
            product_description="Spacious modular sofa"
        )
        self.job = ClassificationJob.objects.create(
            status=ClassificationJob.Status.PENDING,
            total_products=2
        )

    def test_process_classification_job_runs_to_completion(self):
        result = process_classification_job(self.job.id)
        self.assertEqual(result["status"], ClassificationJob.Status.COMPLETED)
        self.assertEqual(result["processed_count"], 2)
        self.assertEqual(result["failed_count"], 0)

        # Check DB records
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, ClassificationJob.Status.COMPLETED)
        self.assertEqual(ClassificationResult.objects.filter(job=self.job, status=ClassificationResult.Status.DONE).count(), 2)

    def test_process_classification_job_resumes_from_crash(self):
        # Pre-seed result for prod1 as 'done'
        ClassificationResult.objects.create(
            product=self.prod1,
            job=self.job,
            predicted_category=self.category,
            confidence=0.88,
            status=ClassificationResult.Status.DONE
        )
        # Pre-seed result for prod2 as 'pending'
        ClassificationResult.objects.create(
            product=self.prod2,
            job=self.job,
            status=ClassificationResult.Status.PENDING
        )
        self.job.processed_count = 1
        self.job.save()

        # Run task - must skip prod1 and only process prod2
        with patch("classification.tasks.classify_product") as mock_classify:
            mock_classify.return_value = {
                "predicted_category": self.category,
                "confidence": 0.75,
                "alternative_categories": [],
                "extracted_attributes": {},
                "needs_manual_review": False
            }
            process_classification_job(self.job.id)

            # mock_classify should only have been called ONCE for prod2
            self.assertEqual(mock_classify.call_count, 1)

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, ClassificationJob.Status.COMPLETED)
        self.assertEqual(self.job.processed_count, 2)


class ClassificationAPITests(APITestCase):
    def setUp(self):
        self.category1 = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/api-cat-1",
            name="Sofas",
            full_name="Furniture > Living Room > Sofas",
            level=2
        )
        self.category2 = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/api-cat-2",
            name="Armchairs",
            full_name="Furniture > Living Room > Armchairs",
            level=2
        )
        self.prod1 = Product.objects.create(
            product_number="API-SKU-001",
            product_name="Plush Sofa",
            product_category="Furniture"
        )
        self.prod2 = Product.objects.create(
            product_number="API-SKU-002",
            product_name="Modern Armchair",
            product_category="Furniture"
        )
        self.job = ClassificationJob.objects.create(
            status=ClassificationJob.Status.COMPLETED,
            total_products=2,
            processed_count=2,
            failed_count=0
        )
        self.res1 = ClassificationResult.objects.create(
            product=self.prod1,
            job=self.job,
            predicted_category=self.category1,
            confidence=0.85,
            alternative_categories=[
                {"category_id": self.category2.id, "name": self.category2.name, "score": 0.15}
            ],
            extracted_attributes={"Color": {"value": "Navy", "confidence": 0.9}},
            needs_manual_review=False,
            status=ClassificationResult.Status.DONE,
            approved=False
        )
        self.res2 = ClassificationResult.objects.create(
            product=self.prod2,
            job=self.job,
            predicted_category=self.category2,
            confidence=0.48,
            needs_manual_review=True,
            status=ClassificationResult.Status.DONE,
            approved=False
        )

    def test_post_jobs_start_job_api(self):
        # Create unclassified product
        Product.objects.create(product_number="API-UNCLASSIFIED-1", product_name="Test Bench")

        with patch("classification.api.process_classification_job"):
            response = self.client.post('/api/jobs/', {"limit": 1, "sync": False}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn("id", response.data)
            self.assertEqual(response.data["total_products"], 1)

    def test_get_job_detail_api(self):
        response = self.client.get(f'/api/jobs/{self.job.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.job.id)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(response.data["progress_percentage"], 100.0)

    def test_get_results_list_with_filters(self):
        # Test default paginated results
        response = self.client.get('/api/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(response.data["count"], 2)

        # Test filter by needs_review=true
        res_filter = self.client.get('/api/results/?needs_review=true')
        self.assertEqual(res_filter.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_filter.data["results"]), 1)
        self.assertEqual(res_filter.data["results"][0]["id"], self.res2.id)

        # Test filter by min_confidence=0.80
        res_conf = self.client.get('/api/results/?min_confidence=0.80')
        self.assertEqual(res_conf.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_conf.data["results"]), 1)
        self.assertEqual(res_conf.data["results"][0]["id"], self.res1.id)

    def test_get_single_result_detail_api(self):
        response = self.client.get(f'/api/results/{self.res1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.res1.id)
        self.assertEqual(len(response.data["alternative_categories"]), 1)
        self.assertIn("Color", response.data["extracted_attributes"])

    def test_patch_result_approve_and_override_api(self):
        payload = {
            "approved": True,
            "override_category_id": self.category2.id,
            "reviewed_by": "qa_lead"
        }
        response = self.client.patch(f'/api/results/{self.res2.id}/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["approved"])
        self.assertFalse(response.data["needs_manual_review"])
        self.assertEqual(response.data["predicted_category"]["id"], self.category2.id)
        self.assertEqual(response.data["reviewed_by"], "qa_lead")

        self.res2.refresh_from_db()
        self.assertTrue(self.res2.approved)
        self.assertFalse(self.res2.needs_manual_review)
        self.assertEqual(self.res2.predicted_category, self.category2)
        self.assertEqual(self.res2.reviewed_by, "qa_lead")

    def test_cors_headers_allowed_origin(self):
        response = self.client.get('/api/health/', HTTP_ORIGIN='http://localhost:5173')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), 'http://localhost:5173')
