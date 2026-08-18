"""
WSGI config for taxonomy_classifier project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxonomy_classifier.settings.dev')

application = get_wsgi_application()
