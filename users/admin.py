from django.contrib import admin

from .models import UserProfile

# Register your models here.
# admin.site.register(Category)
# admin.site.register(Product)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user__email', 'phone_number', 'birthday', 'created_at']
    search_fields = ['phone_number', 'user__email']
    # list_filter = ['phone_number', 'user']
    ordering = ['-created_at']
