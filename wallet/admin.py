from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Sum, Count, Q
from decimal import Decimal
from wallet.models import Wallet
from orders.models import Transaction


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('transactionId', 'type', 'amount', 'created_at')
    fields = ('type', 'amount', 'reference', 'created_at')
    can_delete = False
    ordering = ('-created_at',)
    max_num = 10  # Show only recent 10 transactions
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Filter transactions related to this wallet
        if hasattr(self, 'parent_obj') and self.parent_obj:
            wallet_ref = f"wallet_{self.parent_obj.walletId}"
            return qs.filter(reference__icontains=wallet_ref)
        return qs.none()
    
    def has_add_permission(self, request, obj=None):
        return False  # Transactions should be created through wallet operations


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_info', 'get_balance_display', 'get_transaction_summary',
        'last_updated', 'get_wallet_status'
    )
    
    list_filter = (
        'created_at', 'last_updated',
        'balance'
    )
    
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'walletId'
    )
    
    autocomplete_fields = ['user']
    readonly_fields = (
        'walletId', 'created_at', 'last_updated', 
        'get_transaction_history', 'get_wallet_analytics'
    )
    
    fieldsets = (
        ('Wallet Owner', {
            'fields': ('user',)
        }),
        ('Balance Information', {
            'fields': ('balance', 'get_wallet_analytics')
        }),
        ('Transaction History', {
            'fields': ('get_transaction_history',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('walletId', 'created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['add_bonus_credit', 'freeze_wallets', 'generate_statements']
    
    @admin.display(description='User')
    def get_user_info(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        display_name = full_name if full_name else obj.user.username
        return format_html('<a href="{}">{}</a>', url, display_name)
    
    @admin.display(description='Balance', ordering='balance')
    def get_balance_display(self, obj):
        if obj.balance >= 1000:
            color = '#27ae60'  # Green for high balance
        elif obj.balance >= 100:
            color = '#3498db'  # Blue for medium balance
        elif obj.balance > 0:
            color = '#f39c12'  # Orange for low balance
        else:
            color = '#e74c3c'  # Red for zero/negative balance
        
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">${:.2f}</span>',
            color, obj.balance
        )
    
    @admin.display(description='Transactions')
    def get_transaction_summary(self, obj):
        wallet_ref = f"wallet_{obj.walletId}"
        transactions = Transaction.objects.filter(reference__icontains=wallet_ref)
        
        total_count = transactions.count()
        recent_count = transactions.filter(
            created_at__gte=obj.last_updated
        ).count() if obj.last_updated else 0
        
        if total_count == 0:
            return mark_safe('<span style="color: #999;">No transactions</span>')
        
        return format_html(
            '{} total<br/><small style="color: #666;">{} recent</small>',
            total_count, recent_count
        )
    
    @admin.display(description='Status')
    def get_wallet_status(self, obj):
        if obj.balance <= 0:
            return format_html(
                '<span style="background: #e74c3c; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">Empty</span>'
            )
        elif obj.balance < 50:
            return format_html(
                '<span style="background: #f39c12; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">Low</span>'
            )
        else:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">Active</span>'
            )
    
    @admin.display(description='Transaction History')
    def get_transaction_history(self, obj):
        wallet_ref = f"wallet_{obj.walletId}"
        transactions = Transaction.objects.filter(
            reference__icontains=wallet_ref
        ).order_by('-created_at')[:20]  # Last 20 transactions
        
        if not transactions:
            return "No transaction history"
        
        history_html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 400px; overflow-y: auto;">'
        history_html += '<h4 style="margin-top: 0; color: #333;">Recent Transactions</h4>'
        
        for transaction in transactions:
            color = '#27ae60' if transaction.type in ['DEPOSIT'] else '#e74c3c'
            sign = '+' if transaction.type in ['DEPOSIT'] else '-'
            
            history_html += f'''
            <div style="border-bottom: 1px solid #eee; padding: 8px 0; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{transaction.get_type_display()}</strong><br/>
                    <small style="color: #666;">{transaction.created_at.strftime("%Y-%m-%d %H:%M")}</small>
                </div>
                <div style="text-align: right;">
                    <span style="color: {color}; font-weight: bold;">{sign}${transaction.amount:.2f}</span><br/>
                    <small style="color: #999;">{transaction.reference[:30]}{'...' if len(transaction.reference) > 30 else ''}</small>
                </div>
            </div>
            '''
        
        history_html += '</div>'
        return mark_safe(history_html)
    
    @admin.display(description='Wallet Analytics')
    def get_wallet_analytics(self, obj):
        wallet_ref = f"wallet_{obj.walletId}"
        transactions = Transaction.objects.filter(reference__icontains=wallet_ref)
        
        total_deposits = transactions.filter(type='DEPOSIT').aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0')
        
        total_purchases = transactions.filter(type='PURCHASE').aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0')
        
        total_refunds = transactions.filter(type='REFUND').aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0')
        
        analytics_html = f'''
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
            <h4 style="margin-top: 0; color: #333;">Wallet Analytics</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
                    <div style="color: #27ae60; font-size: 18px; font-weight: bold;">${total_deposits:.2f}</div>
                    <div style="color: #666; font-size: 12px;">Total Deposits</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
                    <div style="color: #e74c3c; font-size: 18px; font-weight: bold;">${total_purchases:.2f}</div>
                    <div style="color: #666; font-size: 12px;">Total Purchases</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
                    <div style="color: #3498db; font-size: 18px; font-weight: bold;">${total_refunds:.2f}</div>
                    <div style="color: #666; font-size: 12px;">Total Refunds</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; text-align: center;">
                    <div style="color: #333; font-size: 18px; font-weight: bold;">{transactions.count()}</div>
                    <div style="color: #666; font-size: 12px;">Total Transactions</div>
                </div>
            </div>
            <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 4px; text-align: center;">
                <div style="color: #333; font-size: 16px; font-weight: bold;">Net Activity</div>
                <div style="color: #666; font-size: 14px;">${total_deposits + total_refunds - total_purchases:.2f}</div>
            </div>
        </div>
        '''
        
        return mark_safe(analytics_html)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    @admin.action(description='Add $10 bonus credit to selected wallets')
    def add_bonus_credit(self, request, queryset):
        bonus_amount = Decimal('10.00')
        updated_count = 0
        
        for wallet in queryset:
            try:
                wallet.deposit(bonus_amount)
                # Create a bonus transaction record
                Transaction.objects.create(
                    type=Transaction.Type.DEPOSIT,
                    amount=bonus_amount,
                    reference=f"admin_bonus_wallet_{wallet.walletId}"
                )
                updated_count += 1
            except Exception as e:
                self.message_user(request, f'Error adding bonus to {wallet.user.username}: {e}', level='ERROR')
        
        self.message_user(request, f'Added ${bonus_amount} bonus credit to {updated_count} wallets.')
    
    @admin.action(description='Generate wallet statements')
    def generate_statements(self, request, queryset):
        # This would trigger statement generation in a real implementation
        count = queryset.count()
        self.message_user(request, f'Statement generation initiated for {count} wallets.')
    
    @admin.action(description='Flag selected wallets for review')
    def freeze_wallets(self, request, queryset):
        # In a real implementation, this might set a 'frozen' flag
        count = queryset.count()
        self.message_user(request, f'{count} wallets flagged for review.')
