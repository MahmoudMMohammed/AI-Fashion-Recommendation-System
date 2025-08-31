from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserProfile, Notification


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ('id', 'updated_at')
    fieldsets = (
        ('Style Analysis', {
            'fields': ('avg_style_vector', 'updated_at'),
            'description': 'AI-generated style preferences based on user interactions'
        }),
    )


class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    readonly_fields = ('created_at', 'read_at')
    fields = ('type', 'title', 'is_read', 'created_at')
    can_delete = False
    max_num = 5  # Show only last 5 notifications
    ordering = ('-created_at',)
    
    def has_add_permission(self, request, obj=None):
        return False  # Don't allow adding notifications from user admin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, NotificationInline)
    
    # Enhanced list display
    list_display = (
        'username', 'get_full_name', 'email', 'get_avatar', 
        'date_joined', 'last_login', 'is_active', 'get_notification_count'
    )
    
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'date_joined',
        'gender', 'last_login'
    )
    
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    
    # Enhanced fieldsets
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': (
                ('first_name', 'last_name'), 
                ('email', 'phone_number'),
                ('date_of_birth', 'gender'),
                'avatar_url'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('last_login', 'date_joined', 'fcm_token'),
            'classes': ('collapse',),
            'description': 'System-generated timestamps and tokens'
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    # Custom display methods
    @admin.display(description='Avatar')
    def get_avatar(self, obj):
        if obj.avatar_url:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar_url.url
            )
        return mark_safe('<span style="color: #999;">No avatar</span>')
    
    @admin.display(description='Full Name', ordering='first_name')
    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return mark_safe('<span style="color: #999;">Not provided</span>')
    
    @admin.display(description='Notifications')
    def get_notification_count(self, obj):
        unread_count = obj.notifications.filter(is_read=False).count()
        total_count = obj.notifications.count()
        
        if unread_count > 0:
            return format_html(
                '<span style="color: #e74c3c; font-weight: bold;">{} unread</span> / {} total',
                unread_count, total_count
            )
        return f"{total_count} total"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('notifications')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'recipient', 'type', 'is_read', 
        'created_at', 'get_action_button'
    )
    
    list_filter = ('type', 'is_read', 'created_at')
    
    search_fields = (
        'title', 'message', 'recipient__username', 
        'recipient__email', 'recipient__first_name', 'recipient__last_name'
    )
    
    autocomplete_fields = ['recipient']
    
    readonly_fields = ('created_at', 'read_at')
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'type', 'title', 'message')
        }),
        ('Payload & Actions', {
            'fields': ('payload', 'action_url'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at', 'read_at')
        })
    )
    
    @admin.display(description='Action')
    def get_action_button(self, obj):
        if obj.action_url:
            return format_html(
                '<a href="{}" target="_blank" style="background: #007cba; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;">View</a>',
                obj.action_url
            )
        return mark_safe('<span style="color: #999;">No action</span>')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    
    @admin.action(description='Mark selected notifications as unread')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
