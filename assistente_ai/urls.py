from django.urls import path
from .views import ChatMordomoView

urlpatterns = [
    # Isso criará o final da rota, ex: .../chat/
    path('chat/', ChatMordomoView.as_view(), name='chat-mordomo'),
]