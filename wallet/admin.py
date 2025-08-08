from django.contrib import admin
from wallet.models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'last_updated')
    search_fields = ['user__username', 'user__email', 'walletId']
    # Making the user field searchable instead of a dropdown is critical
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'last_updated', 'walletId')
