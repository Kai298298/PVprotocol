from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import os
# from django.contrib.gis.db import models as gis_models
# from django.contrib.gis.geos import Point
from accounts.models import Company

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

User = get_user_model()


class Customer(models.Model):
    """Kunden-Model für PV-Anlagen"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customers',
        verbose_name=_('Benutzer')
    )
    
    customer_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Kundennummer')
    )
    
    name = models.CharField(max_length=255, verbose_name=_('Name'), blank=True)
    address = models.TextField(verbose_name=_('Adresse'), blank=True)
    email = models.EmailField(verbose_name=_('E-Mail'), blank=True)
    phone = models.CharField(max_length=50, verbose_name=_('Telefon'), blank=True)
    company_name = models.CharField(max_length=255, verbose_name=_('Unternehmen'), blank=True)
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )
    
    class Meta:
        verbose_name = _('Kunde')
        verbose_name_plural = _('Kunden')
    
    def __str__(self):
        return f"{self.name or self.user} ({self.customer_number})"
    
    def save(self, *args, **kwargs):
        if not self.customer_number:
            # Generiere automatische Kundennummer
            last_customer = Customer.objects.order_by('-id').first()
            if last_customer and last_customer.customer_number and last_customer.customer_number.startswith('KUN'):
                try:
                    last_number = int(last_customer.customer_number[3:])
                except Exception:
                    last_number = last_customer.id
                self.customer_number = f"KUN{last_number + 1:06d}"
            else:
                self.customer_number = "KUN000001"
        super().save(*args, **kwargs)


class PVInstallation(models.Model):
    """PV-Anlage mit Betreiber (Kunde), Profilbild und eindeutiger Anlagennummer."""
    
    STATUS_CHOICES = [
        ('active', 'Aktiv'),
        ('inactive', 'Inaktiv'),
        ('maintenance', 'Wartung'),
        ('error', 'Fehler'),
        ('offline', 'Offline'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Niedrig'),
        ('medium', 'Mittel'),
        ('high', 'Hoch'),
        ('critical', 'Kritisch'),
    ]
    
    installation_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Anlagennummer',
        blank=True,
        null=True
    )
    name = models.CharField(max_length=255, verbose_name='Name')
    size = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Anlagengröße (kWp)', null=True, blank=True)
    location = models.CharField(max_length=255, verbose_name='Standort', null=True, blank=True)
    module_type = models.CharField(max_length=255, verbose_name='Modultyp', null=True, blank=True)
    module_manufacturer = models.CharField(max_length=255, verbose_name='Modulhersteller', null=True, blank=True)
    operator = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='installations', verbose_name='Betreiber/Kunde', null=True, blank=True)
    profile_image = models.ImageField(upload_to='installation_profiles/', blank=True, null=True, verbose_name='Profilbild der Anlage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_power_kw = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Gesamtleistung (kW)',
        null=True,
        blank=True
    )
    number_of_modules = models.PositiveIntegerField(
        verbose_name='Anzahl der Module',
        null=True,
        blank=True
    )
    address = models.CharField(
        max_length=255,
        verbose_name='Adresse',
        null=True,
        blank=True
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Breitengrad'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Längengrad'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_installations',
        verbose_name='Angelegt von'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='installations',
        verbose_name='Firma/Mandant',
        null=True,
        blank=True
    )
    
    # CRM-Felder
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Priorität'
    )
    installation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Inbetriebnahmedatum'
    )
    warranty_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name='Garantieablauf'
    )
    last_maintenance = models.DateField(
        null=True,
        blank=True,
        verbose_name='Letzte Wartung'
    )
    next_maintenance = models.DateField(
        null=True,
        blank=True,
        verbose_name='Nächste Wartung'
    )
    
    # Wechselrichter-Informationen
    inverter_type = models.CharField(
        max_length=255,
        verbose_name='Wechselrichter-Typ',
        null=True,
        blank=True
    )
    inverter_manufacturer = models.CharField(
        max_length=255,
        verbose_name='Wechselrichter-Hersteller',
        null=True,
        blank=True
    )
    inverter_serial = models.CharField(
        max_length=255,
        verbose_name='Wechselrichter-Seriennummer',
        null=True,
        blank=True
    )
    api_endpoint = models.URLField(
        verbose_name='API-Endpunkt für Wechselrichter-Daten',
        null=True,
        blank=True
    )
    api_key = models.CharField(
        max_length=255,
        verbose_name='API-Schlüssel',
        null=True,
        blank=True
    )
    
    # Kontakt-Informationen
    contact_person = models.CharField(
        max_length=255,
        verbose_name='Ansprechpartner',
        null=True,
        blank=True
    )
    contact_phone = models.CharField(
        max_length=50,
        verbose_name='Kontakt-Telefon',
        null=True,
        blank=True
    )
    contact_email = models.EmailField(
        verbose_name='Kontakt-E-Mail',
        null=True,
        blank=True
    )
    
    # Zusätzliche Informationen
    general_notes = models.TextField(
        verbose_name='Allgemeine Notizen',
        blank=True
    )
    tags = models.CharField(
        max_length=500,
        verbose_name='Tags (kommagetrennt)',
        blank=True
    )

    class Meta:
        verbose_name = 'PV-Anlage'
        verbose_name_plural = 'PV-Anlagen'

    def __str__(self):
        return f"{self.name} ({self.location})"
    
    def save(self, *args, **kwargs):
        if not self.installation_number:
            # Generiere automatische Anlagennummer
            last_installation = PVInstallation.objects.order_by('-id').first()
            if last_installation and last_installation.installation_number and last_installation.installation_number.startswith('ANL'):
                try:
                    last_number = int(last_installation.installation_number[3:])
                except Exception:
                    last_number = last_installation.id
                self.installation_number = f"ANL{last_number + 1:06d}"
            else:
                self.installation_number = "ANL000001"
        super().save(*args, **kwargs)
    
    @property
    def coordinates(self):
        """Gibt Koordinaten als Tuple zurück"""
        if getattr(self, 'latitude', None) is not None and getattr(self, 'longitude', None) is not None:
            return (self.longitude, self.latitude)
        return None
    
    @property
    def tag_list(self):
        """Gibt Tags als Liste zurück"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def get_status_color(self):
        """Gibt CSS-Klasse für Status-Farbe zurück"""
        status_colors = {
            'active': 'success',
            'inactive': 'secondary',
            'maintenance': 'warning',
            'error': 'danger',
            'offline': 'dark',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Gibt CSS-Klasse für Prioritäts-Farbe zurück"""
        priority_colors = {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'critical': 'danger',
        }
        return priority_colors.get(self.priority, 'info')


class InstallationImage(models.Model):
    """Bilder für PV-Anlagen"""
    
    installation = models.ForeignKey(
        PVInstallation,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Anlage')
    )
    
    image = models.ImageField(
        upload_to='installation_images/',
        verbose_name=_('Bild')
    )
    
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Beschriftung')
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Hochgeladen am')
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Hochgeladen von')
    )
    
    class Meta:
        verbose_name = _('Anlagenbild')
        verbose_name_plural = _('Anlagenbilder')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.installation.name} - {self.caption or 'Bild'}"


class InstallationDocument(models.Model):
    """Dokumente (z.B. PDF, DOCX) für PV-Anlagen"""
    
    DOCUMENT_TYPES = [
        ('manual', 'Handbuch'),
        ('warranty', 'Garantie'),
        ('certificate', 'Zertifikat'),
        ('maintenance', 'Wartungsprotokoll'),
        ('invoice', 'Rechnung'),
        ('contract', 'Vertrag'),
        ('other', 'Sonstiges'),
    ]
    
    installation = models.ForeignKey(
        PVInstallation,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Anlage')
    )
    file = models.FileField(
        upload_to='installation_documents/',
        verbose_name=_('Dokument')
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='other',
        verbose_name=_('Dokumenttyp')
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Beschreibung')
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Hochgeladen am')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Hochgeladen von')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='installation_documents',
        verbose_name=_('Firma/Mandant'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Anlagendokument')
        verbose_name_plural = _('Anlagendokumente')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.installation.name} - {self.description or 'Dokument'}"


class InstallationNote(models.Model):
    """Notizen für PV-Anlagen (CRM-Funktionalität)"""
    
    NOTE_TYPES = [
        ('general', 'Allgemein'),
        ('maintenance', 'Wartung'),
        ('issue', 'Problem'),
        ('improvement', 'Verbesserung'),
        ('contact', 'Kontakt'),
        ('other', 'Sonstiges'),
    ]
    
    installation = models.ForeignKey(
        PVInstallation,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('Anlage')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Titel')
    )
    content = models.TextField(
        verbose_name=_('Inhalt')
    )
    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPES,
        default='general',
        verbose_name=_('Notiztyp')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Erstellt von')
    )
    is_important = models.BooleanField(
        default=False,
        verbose_name=_('Wichtig')
    )
    
    class Meta:
        verbose_name = _('Anlagennotiz')
        verbose_name_plural = _('Anlagennotizen')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.installation.name} - {self.title}"


class InstallationMaintenance(models.Model):
    """Wartungshistorie für PV-Anlagen"""
    
    MAINTENANCE_TYPES = [
        ('routine', 'Routinewartung'),
        ('repair', 'Reparatur'),
        ('inspection', 'Inspektion'),
        ('cleaning', 'Reinigung'),
        ('upgrade', 'Upgrade'),
        ('emergency', 'Notfall'),
        ('other', 'Sonstiges'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Geplant'),
        ('in_progress', 'In Bearbeitung'),
        ('completed', 'Abgeschlossen'),
        ('cancelled', 'Abgebrochen'),
        ('overdue', 'Überfällig'),
    ]
    
    installation = models.ForeignKey(
        PVInstallation,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        verbose_name=_('Anlage')
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPES,
        verbose_name=_('Wartungstyp')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Titel')
    )
    description = models.TextField(
        verbose_name=_('Beschreibung')
    )
    scheduled_date = models.DateField(
        verbose_name=_('Geplantes Datum')
    )
    completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Abgeschlossen am')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('Status')
    )
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_work',
        verbose_name=_('Techniker')
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Kosten')
    )
    maintenance_notes = models.TextField(
        blank=True,
        verbose_name=_('Wartungsnotizen')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_maintenance',
        verbose_name=_('Erstellt von')
    )
    
    class Meta:
        verbose_name = _('Wartungsprotokoll')
        verbose_name_plural = _('Wartungsprotokolle')
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.installation.name} - {self.title}"


class InstallationDataPoint(models.Model):
    """Datenpunkte für Wechselrichter-API Integration"""
    
    installation = models.ForeignKey(
        PVInstallation,
        on_delete=models.CASCADE,
        related_name='data_points',
        verbose_name=_('Anlage')
    )
    timestamp = models.DateTimeField(
        verbose_name=_('Zeitstempel')
    )
    power_output = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Leistung (kW)')
    )
    energy_today = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Energie heute (kWh)')
    )
    energy_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Gesamtenergie (kWh)')
    )
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Temperatur (°C)')
    )
    voltage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Spannung (V)')
    )
    current = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Strom (A)')
    )
    efficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Wirkungsgrad (%)')
    )
    status_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Status-Code')
    )
    raw_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Rohdaten')
    )
    
    class Meta:
        verbose_name = _('Datenpunkt')
        verbose_name_plural = _('Datenpunkte')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['installation', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.installation.name} - {self.timestamp}"
