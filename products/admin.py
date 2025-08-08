from django.contrib import admin

from products.models import Product, Category, ProductSize, ProductImage


# Define admin for Category with search_fields
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ['name', 'description']  # <-- IMPORTANT


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    search_fields = ['name']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'sku', 'base_price', 'stock_quantity', 'updated_at')

    # We will use this to make the Category selection better
    # Note that 'categories' must be in search_fields of the CategoryAdmin
    autocomplete_fields = ['categories', 'sizes']  # <-- ADD THIS

    list_filter = ('created_at',)  # We will remove the category filter here and rely on search
    search_fields = ['name', 'sku', 'description']  # <-- This is already correctly defined


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('get_product_name', 'alt_text', 'created_at')

    # This is the key change for filtering ProductImages by a searchable Product
    autocomplete_fields = ['product']  # <-- ADD THIS

    list_filter = ('created_at',)

    # A helper method to make the list display nicer
    @admin.display(description='Product Name', ordering='product__name')
    def get_product_name(self, obj):
        return obj.product.name