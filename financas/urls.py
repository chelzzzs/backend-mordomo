from django.urls import path
from .views import ExtratoFinanceiroView

urlpatterns = [
    path('extrato/', ExtratoFinanceiroView.as_view(), name='extrato-financeiro'),
]