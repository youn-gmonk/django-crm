"""
WSGI config for edgecrm project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.middleware import WhiteNoiseMiddleware

# Get the Django application instance
django_application = get_wsgi_application()

# Wrap the Django application with WhiteNoiseMiddleware
application = WhiteNoiseMiddleware(django_application)

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edgecrm.settings')



