from django.urls import path
from .views import WalletViewSet

wallet_detail = WalletViewSet.as_view({'get': 'retrieve'})
wallet_deposit = WalletViewSet.as_view({'post': 'deposit'})

urlpatterns = [
    path('wallet/', wallet_detail, name='wallet-detail'),
    path('wallet/deposit/', wallet_deposit, name='wallet-deposit'),
]