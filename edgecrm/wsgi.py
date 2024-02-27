"""
WSGI config for edgecrm project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application
from whitenoise.middleware import WhiteNoiseMiddleware
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edgecrm.settings')

application = WhiteNoiseMiddleware(get_wsgi_application())



