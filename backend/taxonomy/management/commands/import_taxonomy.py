"""
Django management command to import Shopify's official product taxonomy.
Downloads distribution files or falls back to local data/ directory.
"""

import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from taxonomy.models import Category, Attribute, AttributeValue

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES_URL = "https://raw.githubusercontent.com/Shopify/product-taxonomy/main/dist/en/categories.json"
DEFAULT_ATTRIBUTES_URL = "https://raw.githubusercontent.com/Shopify/product-taxonomy/main/dist/en/attributes.json"


class Command(BaseCommand):
    help = "Download and import Shopify's official Product Taxonomy (Categories, Attributes, and Values)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories-url',
            type=str,
            default=DEFAULT_CATEGORIES_URL,
            help=f"URL for categories.json (default: {DEFAULT_CATEGORIES_URL})"
        )
        parser.add_argument(
            '--attributes-url',
            type=str,
            default=DEFAULT_ATTRIBUTES_URL,
            help=f"URL for attributes.json (default: {DEFAULT_ATTRIBUTES_URL})"
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default=str(settings.BASE_DIR / 'data'),
            help="Local directory for fallback data files (default: project_root/data)"
        )
        parser.add_argument(
            '--local-only',
            action='store_true',
            help="Skip downloading and only read local JSON files from data directory."
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2000,
            help="Batch size for database bulk operations (default: 2000)"
        )

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.MIGRATE_HEADING("=== Shopify Product Taxonomy Importer ==="))

        categories_url = options['categories_url']
        attributes_url = options['attributes_url']
        data_dir = Path(options['data_dir'])
        local_only = options['local_only']
        batch_size = options['batch_size']

        # 1. Load Categories Data
        cat_data = self._fetch_or_load_json(
            name="categories.json",
            url=categories_url,
            local_path=data_dir / 'categories.json',
            local_only=local_only
        )
        if not cat_data:
            raise CommandError("Could not load categories data from remote or local sources. Aborting.")

        # 2. Load Attributes Data
        attr_data = self._fetch_or_load_json(
            name="attributes.json",
            url=attributes_url,
            local_path=data_dir / 'attributes.json',
            local_only=local_only
        )
        if not attr_data:
            raise CommandError("Could not load attributes data from remote or local sources. Aborting.")

        # 3. Extract and normalize categories
        raw_categories = self._extract_categories(cat_data)
        self.stdout.write(f"Parsed {len(raw_categories):,} categories from JSON.")

        # 4. Extract and normalize attributes
        raw_attributes = self._extract_attributes(attr_data)
        self.stdout.write(f"Parsed {len(raw_attributes):,} attributes from JSON.")

        # 5. Database operations (Idempotent bulk import)
        with transaction.atomic():
            cat_count = self._import_categories(raw_categories, batch_size=batch_size)
            attr_count, val_count = self._import_attributes_and_values(raw_attributes, batch_size=batch_size)
            rel_count = self._import_category_attribute_relations(raw_categories, batch_size=batch_size)

        duration = time.time() - start_time
        self.stdout.write(self.style.SUCCESS("\n=== Taxonomy Import Summary ==="))
        self.stdout.write(f"  - Categories imported/updated:       {cat_count:,}")
        self.stdout.write(f"  - Attributes imported/updated:       {attr_count:,}")
        self.stdout.write(f"  - Attribute Values imported/updated: {val_count:,}")
        self.stdout.write(f"  - Category <-> Attribute Links:      {rel_count:,}")
        self.stdout.write(f"  - Completed in:                      {duration:.2f} seconds")
        self.stdout.write(self.style.SUCCESS("Taxonomy import successfully finished!"))

    def _fetch_or_load_json(
        self,
        name: str,
        url: str,
        local_path: Path,
        local_only: bool = False
    ) -> Optional[Any]:
        """
        Attempt to download JSON from URL. If failure, fall back to local file.
        Logs warning if download fails and error if both fail.
        """
        if not local_only:
            self.stdout.write(f"Attempting to download {name} from: {url}")
            data = self._download_json(url)
            if data is not None:
                self.stdout.write(self.style.SUCCESS(f"Successfully downloaded {name} from remote."))
                # Optionally cache to local path
                try:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(local_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                except Exception:
                    pass
                return data
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"WARNING: Remote download of {name} failed. Falling back to local file at {local_path}..."
                    )
                )

        # Local fallback
        if local_path.exists():
            self.stdout.write(f"Reading local file from: {local_path}")
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading local file {local_path}: {e}"))
                return None
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"ERROR: Local fallback file {local_path} does not exist and remote download failed."
                )
            )
            return None

    def _download_json(self, url: str) -> Optional[Any]:
        """Download and parse JSON from a given URL with browser User-Agent."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TaxonomyClassifier/1.0'}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
        except urllib.error.HTTPError as e:
            self.stdout.write(self.style.WARNING(f"HTTP error {e.code} ({e.reason}) when downloading {url}"))
            return None
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Network error when downloading {url}: {e}"))
            return None

    def _extract_categories(self, data: Any) -> List[Dict[str, Any]]:
        """Extract category dicts from various schema variations (verticals, categories, list)."""
        if isinstance(data, dict):
            if 'verticals' in data:
                all_cats = []
                for vertical in data['verticals']:
                    all_cats.extend(vertical.get('categories', []))
                return all_cats
            elif 'categories' in data:
                return data['categories']
            return []
        elif isinstance(data, list):
            return data
        return []

    def _extract_attributes(self, data: Any) -> List[Dict[str, Any]]:
        """Extract attribute dicts from schema variations."""
        if isinstance(data, dict):
            return data.get('attributes', [])
        elif isinstance(data, list):
            return data
        return []

    def _import_categories(self, raw_categories: List[Dict[str, Any]], batch_size: int = 2000) -> int:
        """
        Import categories in level order (root first) so parent FKs can resolve cleanly.
        Uses bulk upsert (update_conflicts=True).
        """
        self.stdout.write("Importing Categories...")
        # Sort by level ascending (0, 1, 2, ...) to ensure parent exists when inserting
        sorted_cats = sorted(raw_categories, key=lambda c: c.get('level', 0))

        category_objs = []
        for cat in sorted_cats:
            cat_id = cat.get('id')
            if not cat_id:
                continue
            name = cat.get('name', '')
            full_name = cat.get('full_name') or name
            level = cat.get('level', 0)
            parent_id = cat.get('parent_id')

            category_objs.append(
                Category(
                    id=cat_id,
                    name=name,
                    full_name=full_name,
                    level=level,
                    parent_id=parent_id
                )
            )

        if not category_objs:
            return 0

        # In Django 5, bulk_create with update_conflicts=True handles upsert across MariaDB/MySQL
        Category.objects.bulk_create(
            category_objs,
            batch_size=batch_size,
            update_conflicts=True,
            update_fields=['name', 'full_name', 'level', 'parent']
        )
        total_count = Category.objects.count()
        self.stdout.write(f"  [+] {total_count:,} categories stored in database.")
        return total_count

    def _import_attributes_and_values(
        self,
        raw_attributes: List[Dict[str, Any]],
        batch_size: int = 2000
    ) -> Tuple[int, int]:
        """
        Import attributes and attribute values in bulk.
        """
        self.stdout.write("Importing Attributes and Allowed Values...")
        attribute_objs = []
        value_objs = []

        for attr in raw_attributes:
            attr_id = attr.get('id')
            if not attr_id:
                continue
            name = attr.get('name', '')
            attribute_objs.append(
                Attribute(
                    id=attr_id,
                    name=name
                )
            )

            for val in attr.get('values', []):
                val_id = val.get('id')
                if not val_id:
                    continue
                val_text = val.get('name') or val.get('value') or ''
                value_objs.append(
                    AttributeValue(
                        id=val_id,
                        attribute_id=attr_id,
                        value=val_text
                    )
                )

        # 1. Bulk upsert Attributes
        if attribute_objs:
            Attribute.objects.bulk_create(
                attribute_objs,
                batch_size=batch_size,
                update_conflicts=True,
                update_fields=['name']
            )

        # 2. Bulk upsert Attribute Values
        if value_objs:
            AttributeValue.objects.bulk_create(
                value_objs,
                batch_size=batch_size,
                update_conflicts=True,
                update_fields=['value', 'attribute']
            )

        attr_count = Attribute.objects.count()
        val_count = AttributeValue.objects.count()
        self.stdout.write(f"  [+] {attr_count:,} attributes stored in database.")
        self.stdout.write(f"  [+] {val_count:,} attribute values stored in database.")
        return attr_count, val_count

    def _import_category_attribute_relations(
        self,
        raw_categories: List[Dict[str, Any]],
        batch_size: int = 2000
    ) -> int:
        """
        Link categories and attributes via the ManyToMany through table.
        """
        self.stdout.write("Linking Categories to Attributes...")
        ThroughModel = Attribute.categories.through

        # Collect unique (category_id, attribute_id) pairs
        seen_pairs = set()
        through_objs = []

        # We also ensure any attribute referenced in categories exists
        existing_attr_ids = set(Attribute.objects.values_list('id', flat=True))
        missing_attrs = []

        for cat in raw_categories:
            cat_id = cat.get('id')
            if not cat_id:
                continue

            for attr in cat.get('attributes', []):
                attr_id = attr.get('id')
                if not attr_id:
                    continue

                if attr_id not in existing_attr_ids:
                    missing_attrs.append(Attribute(id=attr_id, name=attr.get('name', '')))
                    existing_attr_ids.add(attr_id)

                pair = (cat_id, attr_id)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    through_objs.append(
                        ThroughModel(
                            category_id=cat_id,
                            attribute_id=attr_id
                        )
                    )

        if missing_attrs:
            Attribute.objects.bulk_create(
                missing_attrs,
                batch_size=batch_size,
                update_conflicts=True,
                update_fields=['name']
            )

        if through_objs:
            ThroughModel.objects.bulk_create(
                through_objs,
                batch_size=batch_size,
                ignore_conflicts=True
            )

        rel_count = ThroughModel.objects.count()
        self.stdout.write(f"  [+] {rel_count:,} Category <-> Attribute links established.")
        return rel_count
