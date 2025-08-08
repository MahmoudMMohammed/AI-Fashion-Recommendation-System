from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet
from .serializers import WalletSerializer, WalletActionSerializer


class WalletViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for the user's wallet.
    Provides balance and actions to deposit/withdraw.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

    def retrieve(self, request, *args, **kwargs):
        # Provides GET /api/wallet/
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        wallet = self.get_object()
        serializer = WalletActionSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            # Here you would integrate with a payment gateway.
            # Upon successful payment, you call the deposit method.
            wallet.deposit(amount)  # Using the method from your model
            return Response({'status': 'deposit successful', 'new_balance': wallet.balance})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)