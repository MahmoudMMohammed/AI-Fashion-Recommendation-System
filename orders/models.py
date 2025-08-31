from django.db import models
import uuid
from django.db import models
from users.models import User
from products.models import Product
from django.conf import settings


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="orderId")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{str(self.orderId)[:8]} - {self.user.username} ({self.status})"

    def calculate_total(self):
        return sum(item.unit_price * item.quantity for item in self.items.all())


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="itemId")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # NOTE: The diagram missed a link to Product, which is essential.
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of purchase
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} @ ${self.unit_price}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class Transaction(models.Model):
    class Type(models.TextChoices):
        PURCHASE = 'PURCHASE', 'Purchase'
        REFUND = 'REFUND', 'Refund'
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="transactionId")
    type = models.CharField(max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # The reference could be to an Order, a Wallet, etc.
    reference = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - ${self.amount} ({self.reference})"


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="cartId")
    # A cart can be tied to a logged-in user OR just exist for an anonymous session
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart {self.cartId}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="cartItemId")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart"

    @property
    def total_price(self):
        return self.product.get_final_price() * self.quantity
