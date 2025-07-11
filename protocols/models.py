from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from installations.models import PVInstallation
from django.utils import timezone
from django.core.exceptions import ValidationError
import os
from accounts.models import Company

ALLOWED_PROTOCOL_FILE_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.docx']

User = get_user_model()


class ProtocolTemplate(models.Model):
    """Vorlagen für Protokolle"""
    
    class TemplateType(models.TextChoices):
        INSTALLATION = 'installation', _('Installation')
        MAINTENANCE = 'maintenance', _('Wartung')
        REPAIR = 'repair', _('Reparatur')
        INSPECTION = 'inspection', _('Inspektion')
        COMMISSIONING = 'commissioning', _('Inbetriebnahme')
    
    name = models.CharField(
        max_length=200,
        verbose_name=_('Vorlagenname')
    )
    
    template_type = models.CharField(
        max_length=20,
        choices=TemplateType.choices,
        verbose_name=_('Vorlagentyp')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    
    content = models.JSONField(
        verbose_name=_('Vorlageninhalt')
    )
    
    is_active = models.BooleanField(
        verbose_name=_('Aktiv')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Erstellt von')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )
    
    logo = models.ImageField(upload_to='template_logos/', null=True, blank=True, verbose_name='Logo')
    # Branding bleibt für Farben, aber nicht mehr für das Logo
    branding = models.JSONField(
        default=dict,
        verbose_name=_('Branding (Farben)'),
        help_text=_('Branding-Informationen wie Farbschema als JSON, z.B. {"primary_color": "#123456", "secondary_color": "#abcdef"}')
    )

    class Meta:
        verbose_name = _('Protokollvorlage')
        verbose_name_plural = _('Protokollvorlagen')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class TaskImage(models.Model):
    image = models.ImageField(upload_to='task_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name

class TaskNote(models.Model):
    """Notizen für Aufgaben"""
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='notes', verbose_name='Aufgabe')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    content = models.TextField(verbose_name='Notizinhalt')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')
    
    class Meta:
        verbose_name = 'Aufgabennotiz'
        verbose_name_plural = 'Aufgabennotizen'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notiz von {self.author} für {self.task.title}"

class Task(models.Model):
    """Erweiterte Aufgabenverwaltung mit modernen Features"""
    
    class TaskStatus(models.TextChoices):
        TODO = 'todo', _('Zu erledigen')
        IN_PROGRESS = 'in_progress', _('In Bearbeitung')
        REVIEW = 'review', _('Zur Überprüfung')
        COMPLETED = 'completed', _('Abgeschlossen')
        CANCELLED = 'cancelled', _('Abgebrochen')
        ON_HOLD = 'on_hold', _('Pausiert')
    
    class TaskPriority(models.TextChoices):
        LOW = 'low', _('Niedrig')
        MEDIUM = 'medium', _('Mittel')
        HIGH = 'high', _('Hoch')
        URGENT = 'urgent', _('Dringend')
    
    title = models.CharField(max_length=255, verbose_name='Titel')
    description = models.TextField(verbose_name='Beschreibung')
    
    # Status und Priorität
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        verbose_name='Status'
    )
    
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        verbose_name='Priorität'
    )
    
    # Zeitplanung
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fälligkeitsdatum'
    )
    
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Geschätzte Stunden'
    )
    
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Tatsächliche Stunden'
    )
    
    # Beziehungen
    images = models.ManyToManyField(TaskImage, blank=True, related_name='tasks', verbose_name='Bilder')
    installation = models.ForeignKey(
        PVInstallation, 
        on_delete=models.CASCADE, 
        related_name='tasks', 
        verbose_name='Anlage',
        null=True,
        blank=True
    )
    
    assigned_users = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='assigned_tasks', 
        verbose_name='Zugewiesene Mitarbeiter'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='Erstellt von'
    )
    
    # Mandantenfähigkeit
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Firma/Mandant',
        null=True,
        blank=True
    )
    
    # Zeitstempel
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Gestartet am')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Abgeschlossen am')
    
    # Tags für Kategorisierung
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Tags',
        help_text='Komma-getrennte Tags für Kategorisierung'
    )

    class Meta:
        verbose_name = 'Aufgabe'
        verbose_name_plural = 'Aufgaben'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['company']),
        ]

    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        """Gibt Tags als Liste zurück"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def is_overdue(self):
        """Prüft ob die Aufgabe überfällig ist"""
        if self.due_date and self.status not in [self.TaskStatus.COMPLETED, self.TaskStatus.CANCELLED]:
            return timezone.now() > self.due_date
        return False
    
    def get_progress_percentage(self):
        """Berechnet den Fortschritt basierend auf Status"""
        status_progress = {
            self.TaskStatus.TODO: 0,
            self.TaskStatus.IN_PROGRESS: 50,
            self.TaskStatus.REVIEW: 75,
            self.TaskStatus.COMPLETED: 100,
            self.TaskStatus.CANCELLED: 0,
            self.TaskStatus.ON_HOLD: 25,
        }
        return status_progress.get(self.status, 0)
    
    def start_task(self):
        """Startet die Aufgabe"""
        if self.status == self.TaskStatus.TODO:
            self.status = self.TaskStatus.IN_PROGRESS
            self.started_at = timezone.now()
            self.save()
    
    def complete_task(self):
        """Markiert die Aufgabe als abgeschlossen"""
        self.status = self.TaskStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def get_priority_color(self):
        """Gibt Bootstrap-Farbe für Priorität zurück"""
        colors = {
            self.TaskPriority.LOW: 'success',
            self.TaskPriority.MEDIUM: 'info',
            self.TaskPriority.HIGH: 'warning',
            self.TaskPriority.URGENT: 'danger',
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        """Gibt Bootstrap-Farbe für Status zurück"""
        colors = {
            self.TaskStatus.TODO: 'secondary',
            self.TaskStatus.IN_PROGRESS: 'primary',
            self.TaskStatus.REVIEW: 'warning',
            self.TaskStatus.COMPLETED: 'success',
            self.TaskStatus.CANCELLED: 'danger',
            self.TaskStatus.ON_HOLD: 'info',
        }
        return colors.get(self.status, 'secondary')


class Protocol(models.Model):
    """Protokolle für PV-Anlagen"""
    
    class ProtocolStatus(models.TextChoices):
        DRAFT = 'draft', _('Entwurf')
        COMPLETED = 'completed', _('Abgeschlossen')
        SIGNED = 'signed', _('Unterschrieben')
        ARCHIVED = 'archived', _('Archiviert')
    
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel')
    )
    
    installation = models.ForeignKey(
        PVInstallation,
        on_delete=models.CASCADE,
        related_name='protocols',
        verbose_name=_('Anlage')
    )
    
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='protocols',
        verbose_name=_('Aufgabe')
    )
    
    template = models.ForeignKey(
        ProtocolTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Vorlage')
    )
    
    content = models.JSONField(
        verbose_name=_('Protokollinhalt')
    )
    
    status = models.CharField(
        max_length=20,
        choices=ProtocolStatus.choices,
        default=ProtocolStatus.DRAFT,
        verbose_name=_('Status')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_protocols',
        verbose_name=_('Erstellt von')
    )
    
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_protocols',
        verbose_name=_('Unterschrieben von')
    )
    
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Unterschrieben am')
    )
    
    signature_data = models.TextField(
        blank=True,
        verbose_name=_('Unterschriftendaten')
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='protocols',
        verbose_name='Firma/Mandant',
        null=True,
        blank=True
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
        verbose_name = _('Protokoll')
        verbose_name_plural = _('Protokolle')
        ordering = ['-created_at']
    
    def __str__(self):
        if self.installation and hasattr(self.installation, 'name'):
            return f"{self.title} - {self.installation.name}"
        return self.title
    
    def sign_protocol(self, user, signature_data):
        """Protokoll unterschreiben"""
        self.signed_by = user
        self.signed_at = timezone.now()
        self.signature_data = signature_data
        self.status = self.ProtocolStatus.SIGNED
        self.save()


class ProtocolFile(models.Model):
    """Dateien für Protokolle"""
    
    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name=_('Protokoll')
    )
    
    file = models.FileField(
        upload_to='protocol_files/',
        verbose_name=_('Datei')
    )
    
    filename = models.CharField(
        max_length=255,
        verbose_name=_('Dateiname')
    )
    
    file_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Dateityp')
    )
    
    file_size = models.PositiveIntegerField(
        verbose_name=_('Dateigröße (Bytes)')
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Hochgeladen von')
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Hochgeladen am')
    )
    
    class Meta:
        verbose_name = _('Protokolldatei')
        verbose_name_plural = _('Protokolldateien')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        if self.protocol and hasattr(self.protocol, 'title'):
            return f"{self.filename} - {self.protocol.title}"  # type: ignore[attr-defined]
        return self.filename
    
    def clean(self):
        if self.file and self.file.name:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in ALLOWED_PROTOCOL_FILE_EXTENSIONS:
                raise ValidationError(f"Dateityp '{ext}' ist nicht erlaubt. Erlaubt sind: {', '.join(ALLOWED_PROTOCOL_FILE_EXTENSIONS)}")
            if hasattr(self.file, 'file') and hasattr(self.file.file, 'size') and self.file.file.size > 20 * 1024 * 1024:  # type: ignore[attr-defined]
                raise ValidationError("Datei zu groß (max. 20MB erlaubt).")

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.filename and self.file and self.file.name:
            self.filename = self.file.name.split('/')[-1]
        if not self.file_size and self.file and hasattr(self.file, 'file') and hasattr(self.file.file, 'size'):
            self.file_size = self.file.file.size  # type: ignore[attr-defined]
        super().save(*args, **kwargs)
