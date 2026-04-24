from django.urls import path
from .views import ExtratoFinanceiroView
from rest_framework.routers import DefaultRouter
from .views import DespesaFixaViewSet, perfil_usuario


router = DefaultRouter()
router.register(r'despesas-fixas', DespesaFixaViewSet, basename='despesafixa')

urlpatterns = [
    path('extrato/', ExtratoFinanceiroView.as_view(), name='extrato-financeiro'),
    path('perfil/', perfil_usuario, name='perfil'),
    path('', include(router.urls)),
    
]