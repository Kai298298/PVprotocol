from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SubscriptionPlan(models.Model):
    """Abonnement-Pläne für das SaaS-System"""
    
    class PlanType(models.TextChoices):
        BASIC = 'basic', _('Basic')
        PROFESSIONAL = 'professional', _('Professional')
        ENTERPRISE = 'enterprise', _('Enterprise')
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Planname')
    )
    
    plan_type = models.CharField(
        max_length=20,
        choices=PlanType.choices,
        verbose_name=_('Plantyp')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Monatspreis (€)')
    )
    
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Jahrspreis (€)')
    )
    
    max_installations = models.PositiveIntegerField(
        verbose_name=_('Max. Anlagen')
    )
    
    max_users = models.PositiveIntegerField(
        verbose_name=_('Max. Benutzer')
    )
    
    max_storage_gb = models.PositiveIntegerField(
        verbose_name=_('Max. Speicher (GB)')
    )
    
    features = models.JSONField(
        default=list,
        verbose_name=_('Features')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    
    class Meta:
        verbose_name = _('Abonnement-Plan')
        verbose_name_plural = _('Abonnement-Pläne')
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} - {self.price_monthly}€/Monat"


class Subscription(models.Model):
    """Benutzer-Abonnements"""
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', _('Aktiv')
        CANCELLED = 'cancelled', _('Gekündigt')
        EXPIRED = 'expired', _('Abgelaufen')
        PENDING = 'pending', _('Ausstehend')
    
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', _('Monatlich')
        YEARLY = 'yearly', _('Jährlich')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Benutzer')
    )
    
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Plan')
    )
    
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING,
        verbose_name=_('Status')
    )
    
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        verbose_name=_('Abrechnungszyklus')
    )
    
    start_date = models.DateTimeField(
        verbose_name=_('Startdatum')
    )
    
    end_date = models.DateTimeField(
        verbose_name=_('Enddatum')
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Preis')
    )
    
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Zahlungsmethode')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )
    
    class Meta:
        verbose_name = _('Abonnement')
        verbose_name_plural = _('Abonnements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()
        
        if not self.end_date:
            if self.billing_cycle == self.BillingCycle.MONTHLY:
                self.end_date = self.start_date + timedelta(days=30)
            else:
                self.end_date = self.start_date + timedelta(days=365)
        
        if not self.price:
            if self.billing_cycle == self.BillingCycle.MONTHLY:
                self.price = self.plan.price_monthly
            else:
                self.price = self.plan.price_yearly
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Prüft ob das Abonnement aktiv ist"""
        return (
            self.status == self.SubscriptionStatus.ACTIVE and
            self.end_date > timezone.now()
        )
    
    @property
    def days_remaining(self):
        """Tage bis zum Ablauf"""
        if self.end_date:
            remaining = self.end_date - timezone.now()
            return max(0, remaining.days)
        return 0


class Payment(models.Model):
    """Zahlungen für Abonnements"""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Ausstehend')
        COMPLETED = 'completed', _('Abgeschlossen')
        FAILED = 'failed', _('Fehlgeschlagen')
        CANCELLED = 'cancelled', _('Abgebrochen')
        REFUNDED = 'refunded', _('Erstattet')
    
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', _('Kreditkarte')
        BANK_TRANSFER = 'bank_transfer', _('Banküberweisung')
        PAYPAL = 'paypal', _('PayPal')
        STRIPE = 'stripe', _('Stripe')
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Abonnement')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Betrag')
    )
    
    currency = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name=_('Währung')
    )
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_('Status')
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name=_('Zahlungsmethode')
    )
    
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Transaktions-ID')
    )
    
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Zahlungsdatum')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    
    class Meta:
        verbose_name = _('Zahlung')
        verbose_name_plural = _('Zahlungen')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subscription} - {self.amount}{self.currency}"
    
    def complete_payment(self, transaction_id=None):
        """Zahlung als abgeschlossen markieren"""
        self.status = self.PaymentStatus.COMPLETED
        self.payment_date = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()
