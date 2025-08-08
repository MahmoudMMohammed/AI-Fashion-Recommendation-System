from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Wallet
        fields = ['walletId', 'user', 'balance', 'last_updated']
        read_only_fields = ['balance'] # Balance is only modified via actions

class WalletActionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)