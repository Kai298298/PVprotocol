from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Company


class UserAdmin(BaseUserAdmin):
    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.is_admin
    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin:
            return True
        # Mitarbeiter dürfen keine anderen User bearbeiten
        return obj is not None and obj.pk == request.user.pk
    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.is_admin

# admin.site.register(User, UserAdmin)  # Diese Zeile entfernt - doppelte Registrierung
admin.site.register(Company)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Admin-Konfiguration für das Custom User Model"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Persönliche Informationen'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'company', 'address', 'profile_image')
        }),
        (_('Berechtigungen'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Wichtige Daten'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.is_admin
    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin:
            return True
        # Mitarbeiter dürfen keine anderen User bearbeiten
        return obj is not None and obj.pk == request.user.pk
    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.is_admin
