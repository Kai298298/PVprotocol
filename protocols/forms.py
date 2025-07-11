from django import forms
from django.contrib.auth import get_user_model
from .models import Task, TaskNote, TaskImage, ProtocolTemplate
from installations.models import PVInstallation
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class TaskForm(forms.ModelForm):
    """Erweitertes Formular für Aufgaben mit allen modernen Features"""
    
    # Erweiterte Felder für bessere UX
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'placeholder': 'Fälligkeitsdatum wählen'
            }
        ),
        label=_('Fälligkeitsdatum')
    )
    
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_('Zugewiesene Mitarbeiter')
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Tags (komma-getrennt)'
            }
        ),
        label=_('Tags'),
        help_text=_('Komma-getrennte Tags für Kategorisierung')
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'due_date',
            'estimated_hours', 'actual_hours', 'installation', 
            'assigned_users', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Aufgabentitel eingeben'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detaillierte Beschreibung der Aufgabe'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'actual_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'installation': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtere Anlagen basierend auf User-Berechtigungen
        if user and not user.is_superuser:
            self.fields['installation'].queryset = PVInstallation.objects.filter(
                operator__user=user
            )
        
        # Filtere Mitarbeiter basierend auf Mandant
        if user and user.company:
            self.fields['assigned_users'].queryset = User.objects.filter(
                company=user.company,
                is_active=True
            )
    
    def clean_due_date(self):
        """Validiert das Fälligkeitsdatum"""
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise ValidationError(_('Fälligkeitsdatum kann nicht in der Vergangenheit liegen.'))
        return due_date
    
    def clean_actual_hours(self):
        """Validiert die tatsächlichen Stunden"""
        actual_hours = self.cleaned_data.get('actual_hours')
        if actual_hours and actual_hours < 0:
            raise ValidationError(_('Tatsächliche Stunden können nicht negativ sein.'))
        return actual_hours

class TaskNoteForm(forms.ModelForm):
    """Formular für Aufgabennotizen"""
    
    class Meta:
        model = TaskNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notiz eingeben...',
                'style': 'resize: vertical;'
            })
        }
        labels = {
            'content': _('Notiz')
        }

class TaskFilterForm(forms.Form):
    """Formular für Aufgabenfilterung"""
    
    STATUS_CHOICES = [('', _('Alle Status'))] + list(Task.TaskStatus.choices)
    PRIORITY_CHOICES = [('', _('Alle Prioritäten'))] + list(Task.TaskPriority.choices)
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Aufgaben suchen...'
        }),
        label=_('Suche')
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Status')
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Priorität')
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Zugewiesen an')
    )
    
    installation = forms.ModelChoiceField(
        queryset=PVInstallation.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Anlage')
    )
    
    due_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label=_('Fällig ab')
    )
    
    due_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label=_('Fällig bis')
    )
    
    overdue_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Nur überfällige Aufgaben')
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtere basierend auf User-Berechtigungen
        if user and not user.is_superuser:
            self.fields['assigned_to'].queryset = User.objects.filter(
                company=user.company,
                is_active=True
            )
            self.fields['installation'].queryset = PVInstallation.objects.filter(
                operator__user=user
            )

class TaskBulkActionForm(forms.Form):
    """Formular für Bulk-Aktionen auf Aufgaben"""
    
    ACTION_CHOICES = [
        ('', _('Aktion wählen')),
        ('start', _('Aufgaben starten')),
        ('complete', _('Aufgaben abschließen')),
        ('assign', _('Mitarbeiter zuweisen')),
        ('change_status', _('Status ändern')),
        ('change_priority', _('Priorität ändern')),
        ('delete', _('Aufgaben löschen')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    task_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    new_status = forms.ChoiceField(
        choices=Task.TaskStatus.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Neuer Status')
    )
    
    new_priority = forms.ChoiceField(
        choices=Task.TaskPriority.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Neue Priorität')
    )
    
    assign_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_('Zuweisen an')
    ) 

class ProtocolTemplateForm(forms.ModelForm):
    class Meta:
        model = ProtocolTemplate
        fields = ['name', 'template_type', 'description', 'content', 'is_active', 'logo', 'branding']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorlagenname eingeben'}),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Beschreibung der Vorlage'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'branding': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Branding-Informationen als JSON'}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content:
            raise ValidationError(_('Das Feld "Vorlageninhalt" darf nicht leer sein.'))
        # Prüfe, ob es ein valides JSON ist und mindestens ein Feld enthält
        if isinstance(content, str):
            import json
            try:
                content_json = json.loads(content)
            except Exception:
                raise ValidationError(_('Der Vorlageninhalt ist kein valides JSON.'))
        else:
            content_json = content
        if not isinstance(content_json, list) or len(content_json) == 0:
            raise ValidationError(_('Die Vorlage muss mindestens ein Feld enthalten.'))
        return content_json 