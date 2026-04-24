from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from financas.views import DashboardView, perfil_usuario, DespesaFixaViewSet
from assistente_ai.views import ChatMordomoView

router = DefaultRouter()
router.register(r'despesas-fixas', DespesaFixaViewSet, basename='despesas')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/perfil/', perfil_usuario),
    path('api/', include(router.urls)),
    # Rotas de Login / Segurança
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rota do Chat do Mordomo
    path('api/chat/', ChatMordomoView.as_view(), name='chat_mordomo'),

    # A  Rota do Dashboard 
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'), 
]