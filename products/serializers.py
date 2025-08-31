from rest_framework import serializers
from .models import Category, ProductSize, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['categoryId', 'name', 'description']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['sizeId', 'label', 'dimensions']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']


class ProductSerializer(serializers.ModelSerializer):
    # Use nested serializers for read operations to show full details
    categories = CategorySerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    # Use PrimaryKeyRelatedField for write operations
    categories_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Category.objects.all(), source='categories'
    )
    sizes_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=ProductSize.objects.all(), source='sizes'
    )

    # Add a custom field for the calculated price
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'productId', 'name', 'description', 'base_price', 'discount_percent',
            'final_price', 'stock_quantity', 'categories', 'sizes',
            'categories_ids', 'sizes_ids', 'images'
        ]

    def get_final_price(self, obj):
        return obj.get_final_price()


class ProductMiniSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ("productId", "name", "base_price", "images")
