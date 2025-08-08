from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from wallet.models import Wallet
from .models import Order, OrderItem, Transaction, Product, Cart, CartItem
from .serializers import (
    OrderSerializer, TransactionSerializer, CartSerializer,
    AddCartItemSerializer, CartItemSerializer, UpdateCartItemSerializer
)
from .cart import get_or_create_cart


# --- Order and Transaction Views (Now Simpler) ---

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows orders to be viewed.
    Orders are now created only via the cart checkout process, not directly.
    Users can only see their own orders. Admins can see all.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Admins see all orders, regular users only see their own."""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().prefetch_related('items__product')
        return Order.objects.filter(user=user).prefetch_related('items__product')


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing transactions. Admins only.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]


# --- Cart and Cart Item Views (New Structure) ---

class CartViewSet(viewsets.ViewSet):
    """
    A ViewSet for viewing the user's cart and initiating the checkout process.
    Item management is handled by the CartItemViewSet.
    """
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """GET /api/cart/ - Retrieve the current user's or session's cart."""
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def checkout(self, request):
        """
        POST /api/cart/checkout/ - Creates an Order from the cart
        and deducts the total amount from the user's wallet.
        """
        cart = get_or_create_cart(request)
        if not cart.items.exists():
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        order_total = cart.total_price

        try:
            user_wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return Response({'error': "User wallet not found. Please create one first."},
                            status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Create a new order instance
            order = Order.objects.create(user=request.user)
            order_items = [
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.get_final_price()
                ) for item in cart.items.all()
            ]
            OrderItem.objects.bulk_create(order_items)

            try:
                # Attempt to debit from wallet and complete the order
                user_wallet.debit(order_total, reference=f"Order_{order.orderId}")
                order.status = Order.Status.PAID
                order.save()
            except ValueError as e:  # Catches "Insufficient funds"
                # The transaction.atomic() block ensures the order creation is rolled back
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Clear the cart only after a completely successful transaction
            cart.items.all().delete()

        # Return a detailed response of the successful order
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items within a cart.
    Allows for creating (adding), updating (quantity), and deleting items.
    The queryset is dynamically filtered to the current user's/session's cart.
    """
    http_method_names = ['post', 'patch', 'delete']  # No list, retrieve, or full update needed
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return AddCartItemSerializer
        if self.action == 'partial_update':
            return UpdateCartItemSerializer
        # We don't really need a default here, but it's good practice.
        return CartItemSerializer

    def get_queryset(self):
        """Ensures that we only operate on items within the current session's cart."""
        cart = get_or_create_cart(self.request)
        return CartItem.objects.filter(cart=cart)

    def create(self, request, *args, **kwargs):
        """
        Handles adding a product to the cart or increasing its quantity.
        POST /api/cart/items/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        cart = get_or_create_cart(request)

        try:
            product = Product.objects.get(productId=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # get_or_create handles the case where the item is new to the cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        # If the item was not new, we add to its quantity
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Return the created/updated item to the client for confirmation
        response_serializer = CartItemSerializer(cart_item)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)