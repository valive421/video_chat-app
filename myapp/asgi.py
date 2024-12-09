"""
ASGI config for myapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""
import os

from channels.routing import ProtocolTypeRouter ,URLRouter
from django.core.asgi import get_asgi_application
import chat.routing
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # Just HTTP for now. (We can add other protocols later.)
    "websocket":AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpattern)
    )
})
