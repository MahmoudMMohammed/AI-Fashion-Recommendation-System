from decimal import Decimal

from django.db import models

import uuid
from django.db import models
from users.models import User
# Note: Import Transaction from orders.models to implement methods
from orders.models import Transaction


class Wallet(models.Model):
    walletId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # These methods are better handled in a service layer to ensure transactional integrity.
    # Example implementation:
    def deposit(self, amount):
        # ... existing deposit method
        self.balance += Decimal(amount)
        self.save(update_fields=['balance', 'last_updated'])
        Transaction.objects.create(
            type=Transaction.Type.DEPOSIT,
            amount=amount,
            reference=f"wallet_{self.walletId}"
        )

    def debit(self, amount, reference=""):
        """
        Deducts an amount from the wallet balance.
        Raises ValueError if funds are insufficient.
        """
        amount_to_debit = Decimal(amount)
        if self.balance < amount_to_debit:
            raise ValueError("Insufficient funds in wallet.")

        self.balance -= amount_to_debit
        self.save(update_fields=['balance', 'last_updated'])
        Transaction.objects.create(
            type=Transaction.Type.PURCHASE,
            amount=amount_to_debit,
            reference=reference
        )
    def get_balance(self):
        return self.balance
