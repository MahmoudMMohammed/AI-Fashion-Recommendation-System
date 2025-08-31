from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Sum, Count, Avg
from django.contrib.admin import DateFieldListFilter
from orders.models import Order, OrderItem, Transaction, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('itemId', 'get_total_price', 'unit_price')
    fields = ('product', 'quantity', 'unit_price', 'get_total_price')
    autocomplete_fields = ['product']
    can_delete = False  # Orders are records, items shouldn't be deleted
    
    @admin.display(description='Total')
    def get_total_price(self, obj):
        if obj.unit_price and obj.quantity:
            return f"${float(obj.total_price)}"
        return "$0.00"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('cartItemId', 'get_item_total')
    fields = ('product', 'quantity', 'get_item_total')
    autocomplete_fields = ['product']
    
    @admin.display(description='Total')
    def get_item_total(self, obj):
        if obj.product and obj.quantity:
            return f"${float(obj.total_price)}"
        return "$0.00"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    
    list_display = (
        'get_order_number', 'get_customer_info', 'status', 
        'get_items_count', 'get_total_display', 
        'created_at', 'get_status_badge'
    )
    
    list_filter = (
        'status', 
        ('created_at', DateFieldListFilter),
        ('updated_at', DateFieldListFilter)
    )
    
    search_fields = (
        'orderId', 'user__username', 'user__email', 
        'user__first_name', 'user__last_name'
    )
    
    autocomplete_fields = ['user']
    readonly_fields = ('orderId', 'created_at', 'updated_at', 'get_order_summary')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'get_order_summary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('orderId',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'cancel_orders']
    
    @admin.display(description='Order #', ordering='orderId')
    def get_order_number(self, obj):
        return f"#{str(obj.orderId)[:8]}..."
    
    @admin.display(description='Customer')
    def get_customer_info(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        display_name = full_name if full_name else obj.user.username
        return format_html('<a href="{}">{}</a>', url, display_name)
    
    @admin.display(description='Items')
    def get_items_count(self, obj):
        count = obj.items.count()
        total_qty = sum(item.quantity for item in obj.items.all())
        return f"{count} items ({total_qty} units)"
    
    @admin.display(description='Total', ordering='order_total')
    def get_total_display(self, obj):
        total = obj.calculate_total()
        return format_html('<strong>${}</strong>', float(total))
    
    @admin.display(description='Status')
    def get_status_badge(self, obj):
        colors = {
            'PENDING': '#f39c12',
            'PAID': '#3498db', 
            'SHIPPED': '#9b59b6',
            'DELIVERED': '#27ae60',
            'CANCELLED': '#e74c3c'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    
    @admin.display(description='Order Summary')
    def get_order_summary(self, obj):
        items = obj.items.all()
        if not items:
            return "No items"
        
        summary_html = '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
        for item in items[:5]:  # Show max 5 items
            summary_html += f'<div>{item.quantity}x {item.product.name} @ ${item.unit_price}</div>'
        
        if len(items) > 5:
            summary_html += f'<div style="color: #999; font-style: italic;">... and {len(items) - 5} more items</div>'
        
        summary_html += f'<div style="border-top: 1px solid #ddd; margin-top: 8px; padding-top: 8px; font-weight: bold;">Total: ${obj.calculate_total()}</div>'
        summary_html += '</div>'
        
        return mark_safe(summary_html)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items__product').annotate(
            order_total=Sum('items__unit_price')
        )
    
    @admin.action(description='Mark selected orders as paid')
    def mark_as_paid(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(status='PAID')
        self.message_user(request, f'{updated} orders marked as paid.')
    
    @admin.action(description='Mark selected orders as shipped')
    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status='PAID').update(status='SHIPPED')
        self.message_user(request, f'{updated} orders marked as shipped.')
    
    @admin.action(description='Mark selected orders as delivered')
    def mark_as_delivered(self, request, queryset):
        updated = queryset.filter(status='SHIPPED').update(status='DELIVERED')
        self.message_user(request, f'{updated} orders marked as delivered.')
    
    @admin.action(description='Cancel selected orders')
    def cancel_orders(self, request, queryset):
        updated = queryset.exclude(status__in=['DELIVERED', 'CANCELLED']).update(status='CANCELLED')
        self.message_user(request, f'{updated} orders cancelled.')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
    
    list_display = (
        'get_cart_info', 'get_owner_info', 'get_items_count', 
        'get_total_display', 'created_at', 'updated_at'
    )
    
    list_filter = (
        'created_at', 'updated_at'
    )
    
    search_fields = (
        'user__username', 'user__email', 'session_key', 'cartId'
    )
    
    readonly_fields = (
        'cartId', 'created_at', 'updated_at', 'get_cart_details'
    )
    
    fieldsets = (
        ('Cart Owner', {
            'fields': ('user', 'session_key'),
            'description': 'Either user OR session_key should be set for anonymous carts'
        }),
        ('Cart Details', {
            'fields': ('get_cart_details',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('cartId',),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Cart ID')
    def get_cart_info(self, obj):
        return f"Cart #{str(obj.cartId)[:8]}"
    
    @admin.display(description='Owner')
    def get_owner_info(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        elif obj.session_key:
            return format_html(
                '<span style="color: #999;">Session: {}</span>', 
                obj.session_key[:12] + '...' if len(obj.session_key) > 12 else obj.session_key
            )
        return mark_safe('<span style="color: #e74c3c;">No owner</span>')
    
    @admin.display(description='Items')
    def get_items_count(self, obj):
        count = obj.items.count()
        if count > 0:
            total_qty = sum(item.quantity for item in obj.items.all())
            return f"{count} items ({total_qty} units)"
        return "Empty cart"
    
    @admin.display(description='Total')
    def get_total_display(self, obj):
        total = obj.total_price
        if total > 0:
            return format_html('<strong>${}</strong>', float(total))
        return "$0.00"
    
    @admin.display(description='Cart Contents')
    def get_cart_details(self, obj):
        items = obj.items.all()
        if not items:
            return "Empty cart"
        
        details_html = '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
        for item in items[:10]:  # Show max 10 items
            details_html += f'<div>{item.quantity}x {item.product.name} @ ${item.product.get_final_price()}</div>'
        
        if len(items) > 10:
            details_html += f'<div style="color: #999; font-style: italic;">... and {len(items) - 10} more items</div>'
        
        details_html += f'<div style="border-top: 1px solid #ddd; margin-top: 8px; padding-top: 8px; font-weight: bold;">Total: ${float(obj.total_price)}</div>'
        details_html += '</div>'
        
        return mark_safe(details_html)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items__product')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'get_transaction_id', 'type', 'get_amount_display', 
        'reference', 'created_at', 'get_type_badge'
    )
    
    list_filter = (
        'type', 
        ('created_at', DateFieldListFilter),
        'amount'
    )
    
    search_fields = ('reference', 'transactionId', 'amount')
    readonly_fields = ('transactionId', 'created_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('type', 'amount', 'reference')
        }),
        ('System Info', {
            'fields': ('transactionId', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Transaction ID')
    def get_transaction_id(self, obj):
        return f"#{str(obj.transactionId)[:8]}"
    
    @admin.display(description='Amount', ordering='amount')
    def get_amount_display(self, obj):
        if obj.type in ['REFUND', 'WITHDRAWAL']:
            return format_html('<span style="color: #e74c3c;">-${}</span>', obj.amount)
        return format_html('<span style="color: #27ae60;">+${}</span>', obj.amount)
    
    @admin.display(description='Type')
    def get_type_badge(self, obj):
        colors = {
            'PURCHASE': '#3498db',
            'REFUND': '#e74c3c',
            'DEPOSIT': '#27ae60',
            'WITHDRAWAL': '#f39c12'
        }
        color = colors.get(obj.type, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_type_display()
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'get_order_info', 'get_product_info', 'quantity', 
        'unit_price', 'get_total_price', 'get_order_status'
    )
    
    list_filter = (
        'order__status', 'order__created_at', 'product__categories'
    )
    
    search_fields = (
        'order__orderId', 'order__user__username', 
        'product__name', 'product__sku'
    )
    
    autocomplete_fields = ['order', 'product']
    readonly_fields = ('itemId', 'get_total_price')
    
    @admin.display(description='Order')
    def get_order_info(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.orderId])
        return format_html(
            '<a href="{}">Order #{}</a>', 
            url, str(obj.order.orderId)[:8]
        )
    
    @admin.display(description='Product')
    def get_product_info(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.productId])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @admin.display(description='Total')
    def get_total_price(self, obj):
        return f"${obj.total_price}"
    
    @admin.display(description='Order Status')
    def get_order_status(self, obj):
        return obj.order.get_status_display()


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'get_cart_info', 'get_product_info', 'quantity', 'get_item_total'
    )
    
    list_filter = ('cart__created_at', 'product__categories')
    
    search_fields = (
        'cart__cartId', 'cart__user__username', 
        'product__name', 'product__sku'
    )
    
    autocomplete_fields = ['cart', 'product']
    readonly_fields = ('cartItemId', 'get_item_total')
    
    @admin.display(description='Cart')
    def get_cart_info(self, obj):
        url = reverse('admin:orders_cart_change', args=[obj.cart.cartId])
        owner = obj.cart.user.username if obj.cart.user else 'Anonymous'
        return format_html('<a href="{}">{} Cart</a>', url, owner)
    
    @admin.display(description='Product')
    def get_product_info(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.productId])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    
    @admin.display(description='Total')
    def get_item_total(self, obj):
        return f"${obj.total_price}"
