"""
ASGI config for taxonomy_classifier project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxonomy_classifier.settings.dev')

application = get_asgi_application()
