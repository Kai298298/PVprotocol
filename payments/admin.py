from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SubscriptionPlan, Subscription, Payment


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Abonnement-Pläne"""
    
    list_display = ('name', 'plan_type', 'price_monthly', 'price_yearly', 'max_installations', 'max_users', 'is_active')
    list_filter = ('plan_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('price_monthly',)
    
    fieldsets = (
        (_('Grundinformationen'), {
            'fields': ('name', 'plan_type', 'description', 'is_active')
        }),
        (_('Preise'), {
            'fields': ('price_monthly', 'price_yearly')
        }),
        (_('Limits'), {
            'fields': ('max_installations', 'max_users', 'max_storage_gb')
        }),
        (_('Features'), {
            'fields': ('features',)
        }),
        (_('Zeitstempel'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Abonnements"""
    
    list_display = ('user', 'plan', 'status', 'billing_cycle', 'price', 'start_date', 'end_date')
    list_filter = ('status', 'billing_cycle', 'start_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'plan__name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Grundinformationen'), {
            'fields': ('user', 'plan', 'status')
        }),
        (_('Abrechnung'), {
            'fields': ('billing_cycle', 'price', 'payment_method')
        }),
        (_('Zeitraum'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Zeitstempel'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin-Konfiguration für Zahlungen"""
    
    list_display = ('subscription', 'amount', 'currency', 'status', 'payment_method', 'payment_date')
    list_filter = ('status', 'payment_method', 'currency', 'created_at')
    search_fields = ('subscription__user__username', 'transaction_id')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Grundinformationen'), {
            'fields': ('subscription', 'amount', 'currency', 'status')
        }),
        (_('Zahlungsdetails'), {
            'fields': ('payment_method', 'transaction_id', 'payment_date')
        }),
        (_('Zeitstempel'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
