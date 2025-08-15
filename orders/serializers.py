from rest_framework import serializers
from .models import Order, OrderItem, Transaction
from products.serializers import ProductSerializer  # Reuse product serializer
from .models import Cart, CartItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = OrderItem
        fields = ['itemId', 'product', 'product_id', 'unit_price', 'quantity']
        read_only_fields = ['unit_price']  # Price is set automatically


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = serializers.StringRelatedField(read_only=True)  # Show username on read
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='calculate_total')

    class Meta:
        model = Order
        fields = ['orderId', 'user', 'status', 'created_at', 'items', 'total']
        read_only_fields = ['status']  # Status managed by backend logic

    def create(self, validated_data):
        from products.models import Product

        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            product = Product.objects.get(productId=item_data['product_id'])
            # Here you should lock the product row to prevent race conditions
            # and verify stock quantity before creating the OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.get_final_price()  # Record price at time of order
            )
            # You would also decrease product.stock_quantity here
        return order


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['cartItemId', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['cartId', 'items', 'total_price', 'updated_at']


# A simple serializer for adding/updating items in the cart
class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']
