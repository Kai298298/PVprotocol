from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Customer, PVInstallation, InstallationImage


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Kunden"""
    
    list_display = ('customer_number', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('customer_number', 'user__username', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'customer_number')
        }),
        (_('Zeitstempel'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('customer_number', 'created_at', 'updated_at')


@admin.register(PVInstallation)
class PVInstallationAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für PV-Anlagen"""
    
    list_display = ('name', 'size', 'location', 'module_type', 'module_manufacturer', 'operator', 'created_at')
    search_fields = ('name', 'location', 'module_type', 'module_manufacturer', 'operator__name')
    list_filter = ('module_type', 'module_manufacturer', 'operator')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Grundinformationen', {'fields': ('name', 'description', 'operator')}),
        ('Technische Daten', {'fields': ('size', 'module_type', 'module_manufacturer')}),
        ('Standort', {'fields': ('location', 'profile_image')}),
        ('Zeitstempel', {'fields': ('created_at', 'updated_at')}),
        ('Verantwortliche', {'fields': ('created_by',)}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InstallationImage)
class InstallationImageAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Anlagenbilder"""
    
    list_display = ('installation', 'caption', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('installation__name', 'caption')
    ordering = ('-uploaded_at',)
    
    fieldsets = (
        (None, {
            'fields': ('installation', 'image', 'caption')
        }),
        (_('Upload-Informationen'), {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('uploaded_at',)
