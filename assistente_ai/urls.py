from django.urls import path
from .views import ChatMordomoView

urlpatterns = [
    path('chat/', ChatMordomoView.as_view(), name='chat-mordomo'),
]