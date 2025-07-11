from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ProtocolTemplate, Task, Protocol, ProtocolFile, TaskImage


@admin.register(ProtocolTemplate)
class ProtocolTemplateAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Protokollvorlagen"""
    
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'description', 'content', 'is_active')
        }),
        (_('Erstellung'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Aufgaben"""
    
    list_display = ('title', 'installation', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'installation__name')
    list_filter = ('installation',)
    filter_horizontal = ('assigned_users', 'images')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Grundinformationen'), {
            'fields': ('title', 'description', 'task_type', 'installation')
        }),
        (_('Status & Priorität'), {
            'fields': ('status', 'priority', 'due_date', 'completed_at')
        }),
        (_('Zuweisung'), {
            'fields': ('assigned_to', 'created_by')
        }),
        (_('Zeitstempel'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Protokolle"""
    
    list_display = ('title', 'installation', 'status', 'created_by', 'signed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'installation__name', 'created_by__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Grundinformationen'), {
            'fields': ('title', 'installation', 'task', 'template')
        }),
        (_('Inhalt & Status'), {
            'fields': ('content', 'status')
        }),
        (_('Unterschrift'), {
            'fields': ('signed_by', 'signed_at', 'signature_data')
        }),
        (_('Erstellung'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProtocolFile)
class ProtocolFileAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Protokolldateien"""
    
    list_display = ('filename', 'protocol', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('filename', 'protocol__title')
    ordering = ('-uploaded_at',)
    
    fieldsets = (
        (None, {
            'fields': ('protocol', 'file', 'filename', 'file_type', 'file_size')
        }),
        (_('Upload-Informationen'), {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('filename', 'file_type', 'file_size', 'uploaded_at')

@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'uploaded_at')
