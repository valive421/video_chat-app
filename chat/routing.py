from django.urls import re_path
from . import consumers

websocket_urlpattern=[
    re_path(r'',consumers.ChatConsumer.as_asgi()),
]