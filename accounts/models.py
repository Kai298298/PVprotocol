from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class Company(models.Model):
    """Mandant/Firma für Multi-Tenancy"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Firmenname'))
    address = models.TextField(blank=True, verbose_name=_('Firmenadresse'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Firma')
        verbose_name_plural = _('Firmen')

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User Model mit Rollen für PV-Protokoll System"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        EMPLOYEE = 'employee', 'Mitarbeiter'
        GUEST = 'guest', 'Gast'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name='Rolle'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Telefonnummer')
    )
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Firma/Mandant')
    )
    
    address = models.TextField(
        blank=True,
        verbose_name=_('Adresse')
    )
    
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        verbose_name=_('Profilbild')
    )

    # SaaS-Plan-Logik
    class PlanChoices(models.TextChoices):
        BASIC = 'basic', _('Basic (1 Anlage, 1 User)')
        PREMIUM = 'premium', _('Premium (bis 10 Anlagen, Multi-User, 20€/User)')
        ENTERPRISE = 'enterprise', _('Enterprise (unbegrenzt, Multi-User, Preis auf Anfrage)')

    plan = models.CharField(
        max_length=20,
        choices=PlanChoices.choices,
        default=PlanChoices.BASIC,
        verbose_name=_('SaaS-Plan')
    )

    company_logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        verbose_name=_('Firmenlogo')
    )
    
    # E-Mail-Benachrichtigungsoptionen
    notify_on_new_employee = models.BooleanField(
        default=False,
        verbose_name='E-Mail bei neuen Mitarbeitern'
    )
    notify_on_role_change = models.BooleanField(
        default=False,
        verbose_name='E-Mail bei Rollenänderung'
    )
    notify_on_new_task = models.BooleanField(
        default=False,
        verbose_name='E-Mail bei neuen/zugewiesenen Aufgaben'
    )
    notify_on_new_installation = models.BooleanField(
        default=False,
        verbose_name='E-Mail bei neu angelegten Anlagen'
    )
    notify_on_maintenance_done = models.BooleanField(
        default=False,
        verbose_name='E-Mail bei abgeschlossener Wartung'
    )
    
    class Meta:
        verbose_name = _('Benutzer')
        verbose_name_plural = _('Benutzer')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE
    
    @property
    def is_guest(self):
        return self.role == self.Role.GUEST


class Customer(models.Model):
    """Kundenmodell, unabhängig von Usern."""
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    address = models.TextField(blank=True, verbose_name=_('Adresse'))
    email = models.EmailField(blank=True, verbose_name=_('E-Mail'))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_('Telefon'))
    company_name = models.CharField(max_length=255, blank=True, verbose_name=_('Unternehmen'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Kunde')
        verbose_name_plural = _('Kunden')

    def __str__(self):
        return f"{self.name} ({self.company_name})"


class Invitation(models.Model):
    """Einladungsmodell für neue Mitarbeiter"""
    email = models.EmailField(verbose_name=_('E-Mail-Adresse'))
    role = models.CharField(
        max_length=20, 
        choices=User.Role.choices, 
        default=User.Role.EMPLOYEE, 
        verbose_name=_('Rolle')
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        verbose_name=_('Unternehmen')
    )
    token = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        verbose_name=_('Einladungstoken')
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name=_('Erstellt von')
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Erstellt am')
    )
    expires_at = models.DateTimeField(verbose_name=_('Gültig bis'))
    is_used = models.BooleanField(
        default=False, 
        verbose_name=_('Bereits verwendet')
    )
    
    class Meta:
        verbose_name = _('Einladung')
        verbose_name_plural = _('Einladungen')
        ordering = ['-created_at']

    def __str__(self):
        return f"Einladung für {self.email} ({self.role})"

    def is_expired(self):
        """Prüft ob die Einladung abgelaufen ist"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Prüft ob die Einladung gültig ist"""
        return not self.is_used and not self.is_expired()

    def get_invitation_url(self, request):
        """Generiert die Einladungs-URL"""
        return request.build_absolute_uri(f'/accounts/invite/{self.token}/')
