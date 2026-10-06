"""
ASGI config for office_system project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""
#จุดเชื่อมให้เว็บ server แบบ ASGI
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'office_system.settings')

application = get_asgi_application()
