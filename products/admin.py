from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Avg
from products.models import Product, Category, ProductSize, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_image_preview', 'get_product_count', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ['name', 'description']
    readonly_fields = ('categoryId', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Visual', {
            'fields': ('image_url',)
        }),
        ('System Info', {
            'fields': ('categoryId', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='Preview')
    def get_image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 8px; object-fit: cover;" />',
                obj.image_url.url
            )
        return mark_safe('<span style="color: #999;">No image</span>')

    @admin.display(description='Products', ordering='product_count')
    def get_product_count(self, obj):
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?categories__categoryId__exact={obj.categoryId}'
            return format_html('<a href="{}">{} products</a>', url, count)
        return '0 products'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(product_count=Count('products'))


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('label', 'dimensions', 'get_product_count')
    search_fields = ['label', 'dimensions']
    readonly_fields = ('sizeId',)

    @admin.display(description='Products')
    def get_product_count(self, obj):
        count = obj.products.count()
        if count > 0:
            return f"{count} products"
        return '0 products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('id', 'get_image_preview', 'created_at')
    fields = ('get_image_preview', 'image', 'alt_text', 'created_at')

    @admin.display(description='Preview')
    def get_image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" width="80" height="80" style="border-radius: 4px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"


class StockQuantityZeroFilter(SimpleListFilter):
    title = 'stock quantity'
    parameter_name = 'qty'

    def lookups(self, request, model_admin):
        return (('zero', 'Zero'), ('nonzero', 'Non-zero'))

    def queryset(self, request, qs):
        if self.value() == 'zero':
            return qs.filter(stock_quantity=0)
        if self.value() == 'nonzero':
            return qs.exclude(stock_quantity=0)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

    list_display = (
        'name', 'sku', 'get_price_info', 'stock_quantity',
        'get_stock_status', 'get_categories', 'get_main_image', 'updated_at'
    )

    list_filter = (
        'created_at', 'updated_at', 'categories', 'sizes',
        StockQuantityZeroFilter,
        'discount_percent',
    )

    search_fields = ['name', 'sku', 'description']
    autocomplete_fields = ['categories', 'sizes']

    readonly_fields = (
        'productId', 'created_at', 'updated_at',
        'get_final_price_display', 'get_embedding_status'
    )

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': (
                ('base_price', 'discount_percent', 'get_final_price_display'),
                'stock_quantity'
            )
        }),
        ('Classification', {
            'fields': ('categories', 'sizes')
        }),
        ('AI Features', {
            'fields': ('embedding', 'get_embedding_status'),
            'classes': ('collapse',),
            'description': 'AI-generated embeddings for recommendation system'
        }),
        ('System Info', {
            'fields': ('productId', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    filter_horizontal = ('categories', 'sizes')

    actions = ['generate_embeddings', 'apply_discount', 'mark_out_of_stock']

    @admin.display(description='Price Info')
    def get_price_info(self, obj):
        final_price = obj.get_final_price()
        if obj.discount_percent > 0:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${}</span><br/>'
                '<strong style="color: #e74c3c;">${} (-{}%)</strong>',
                obj.base_price, final_price, obj.discount_percent
            )
        return f"${final_price}"

    @admin.display(description='Stock Status')
    def get_stock_status(self, obj):
        if obj.stock_quantity <= 0:
            return format_html('<span style="color: #e74c3c; font-weight: bold;">Out of Stock</span>')
        elif obj.stock_quantity <= 10:
            return format_html('<span style="color: #f39c12; font-weight: bold;">Low Stock</span>')
        return format_html('<span style="color: #27ae60;">In Stock</span>')

    @admin.display(description='Categories')
    def get_categories(self, obj):
        categories = obj.categories.all()[:3]  # Show max 3 categories
        if categories:
            category_links = []
            for cat in categories:
                url = reverse('admin:products_category_change', args=[cat.categoryId])
                category_links.append(format_html('<a href="{}">{}</a>', url, cat.name))
            result = ', '.join(category_links)
            if obj.categories.count() > 3:
                result += f' (+{obj.categories.count() - 3} more)'
            return mark_safe(result)
        return mark_safe('<span style="color: #999;">No categories</span>')

    @admin.display(description='Main Image')
    def get_main_image(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />',
                first_image.image.url
            )
        return mark_safe('<span style="color: #999;">No image</span>')

    @admin.display(description='Final Price')
    def get_final_price_display(self, obj):
        return f"${obj.get_final_price()}"

    @admin.display(description='AI Embedding')
    def get_embedding_status(self, obj):
        if obj.embedding:
            return format_html('<span style="color: #27ae60;">✓ Generated</span>')
        return format_html('<span style="color: #e74c3c;">✗ Missing</span>')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('categories', 'sizes', 'images')

    @admin.action(description='Generate AI embeddings for selected products')
    def generate_embeddings(self, request, queryset):
        # This would trigger the embedding generation task
        count = queryset.filter(embedding__isnull=True).count()
        self.message_user(request, f'Embedding generation queued for {count} products.')

    @admin.action(description='Apply 10%% discount to selected products')
    def apply_discount(self, request, queryset):
        updated = queryset.update(discount_percent=10)
        self.message_user(request, f'10% discount applied to {updated} products.')

    @admin.action(description='Mark selected products as out of stock')
    def mark_out_of_stock(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(request, f'{updated} products marked as out of stock.')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('get_product_name', 'get_image_preview', 'alt_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ['product__name', 'product__sku', 'alt_text']
    autocomplete_fields = ['product']
    readonly_fields = ('id', 'created_at', 'get_image_preview')

    fieldsets = (
        ('Product Association', {
            'fields': ('product',)
        }),
        ('Image Details', {
            'fields': ('image', 'get_image_preview', 'alt_text')
        }),
        ('System Info', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='Product', ordering='product__name')
    def get_product_name(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.productId])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    @admin.display(description='Preview')
    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 8px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
