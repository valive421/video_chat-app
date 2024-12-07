from django.urls import path
from .views import main_view,redirect_to_chat

urlpatterns=[
    path('', redirect_to_chat, name='redirect-chat'), 
    path('<str:username>/', main_view, name='main-view'),
    ]