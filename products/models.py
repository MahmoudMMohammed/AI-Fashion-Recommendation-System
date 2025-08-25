from decimal import Decimal

import uuid
from django.db import models
from pgvector.django import VectorField, HnswIndex, IvfflatIndex


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="categoryId")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image_url = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductSize(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="sizeId")
    label = models.CharField(max_length=50)  # e.g., "S", "M", "42"
    dimensions = models.CharField(max_length=100, blank=True)  # e.g., "32x34"


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, name="productId")
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock_quantity = models.IntegerField()
    embedding = VectorField(dimensions=2048, null=True, blank=True)

    categories = models.ManyToManyField(Category, related_name='products')
    sizes = models.ManyToManyField(ProductSize, related_name='products')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_final_price(self):
        discount = self.discount_percent / Decimal('100')
        return self.base_price * (Decimal('1') - discount)

    def is_in_stock(self, qty):
        return self.stock_quantity >= qty

    # class Meta:
    #     indexes = [
    #         HnswIndex(
    #             name="emb_hnsw_cos",
    #             fields=["embedding"],
    #             m=16,  # graph connectivity (good default)
    #             ef_construction=64,  # build-time accuracy
    #             opclasses=["vector_cosine_ops"]
    #         )
    #     ]
    
    # class Meta:
    #     indexes = [
    #         IvfflatIndex(
    #             name="emb_ivf_cos",
    #             fields=["embedding"],
    #             lists=100,
    #             opclasses=["vector_cosine_ops"]
    #         )
    #     ]

    class Meta:
        indexes = []


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"
