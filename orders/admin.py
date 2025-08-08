from django.contrib import admin

from orders.models import Order, OrderItem, Transaction, Cart, CartItem


from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Cart, CartItem, Transaction

# --- Inlines for Displaying Related Items ---

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Don't show empty forms on existing orders
    autocomplete_fields = ['product']
    readonly_fields = ('unit_price',)
    fields = ('product', 'quantity', 'unit_price')
    can_delete = False  # Orders are records, items shouldn't be deleted

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    autocomplete_fields = ['product']

# --- ModelAdmin Registrations ---

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('orderId', 'user', 'status', 'get_total', 'created_at')
    list_filter = ('status', 'created_at')
    autocomplete_fields = ['user']
    search_fields = ['orderId', 'user__username', 'user__email']
    date_hierarchy = 'created_at'

    @admin.display(description='Total')
    def get_total(self, obj):
        return f"${obj.calculate_total():.2f}"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    list_display = ('get_cart_owner', 'get_total', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ['user__username', 'session_key']
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Owner')
    def get_cart_owner(self, obj):
        return obj.user.username if obj.user else f"Session: {obj.session_key[:8]}..."

    @admin.display(description='Total')
    def get_total(self, obj):
        return f"${obj.total_price:.2f}"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transactionId', 'type', 'amount', 'reference', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ['reference', 'transactionId']
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

# Note: We don't need a separate admin for CartItem or OrderItem
# because they are best managed through their parent inlines.
# If you wanted one, you would create it like this:
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'quantity', 'unit_price')
#     autocomplete_fields = ['order', 'product']
