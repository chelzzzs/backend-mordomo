from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Suas Views
from assistente_ai.views import ChatMordomoView
from financas.views import DashboardView  # <-- 1. Importando a view do saldo

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rotas de Login / Segurança
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rota do Chat do Mordomo
    path('api/chat/', ChatMordomoView.as_view(), name='chat_mordomo'),

    # <-- 2. A nova Rota do Dashboard que o React vai chamar
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'), 
]