# test_product.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fashionRecommendationSystem.settings')
django.setup()

from products.models import Product, ProductImage
from django.core.files import File

# إنشاء منتج مع صورة
product = Product.objects.create(
    name="Test Product",
    sku="TestProductTest3e5",
    description="Test description",
    base_price=99.99,
    stock_quantity=10
)

# إضافة صورة
with open("test_image.jpg", 'rb') as img_file:
    ProductImage.objects.create(
        product=product,
        image=File(img_file),
        alt_text="Test image"
    )

# التحقق
product.refresh_from_db()
print(f"✅ Embedding created: {product.embedding is not None}")