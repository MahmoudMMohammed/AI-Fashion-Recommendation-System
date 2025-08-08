from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    search_fields = ('username', 'first_name', 'last_name', 'email')


# Register directly (no need to unregister if it wasn't registered)
admin.site.register(User, UserAdmin)
