from rest_framework import viewsets, permissions
from .models import Product, Category, ProductSize, ProductImage
from .serializers import ProductSerializer, CategorySerializer, ProductSizeSerializer, ProductImageSerializer
from rest_framework.parsers import MultiPartParser, FormParser


class ProductViewSet(viewsets.ModelViewSet):
    """API endpoint for products."""
    queryset = Product.objects.all().prefetch_related('categories', 'sizes')
    serializer_class = ProductSerializer

    def get_permissions(self):
        # Allow anyone to view products (list, retrieve)
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        # But only admins to create, update, or delete them
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductSizeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing product sizes."""
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer
    permission_classes = [permissions.AllowAny]


class ProductImageViewSet(viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Filter images by the product ID in the URL
        return ProductImage.objects.filter(product_id=self.kwargs['product_pk'])

    def perform_create(self, serializer):
        # Automatically associate the image with the product from the URL
        serializer.save(product_id=self.kwargs['product_pk'])
