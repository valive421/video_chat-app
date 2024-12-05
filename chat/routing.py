from django.urls import re_path
from . import consumers

websocket_urlpattern = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi(), name='video_chat'),
    re_path(r'ws/game/$', consumers.GameConsumer.as_asgi(), name='game'),
]
