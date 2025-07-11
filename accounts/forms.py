from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User, Invitation
from django.utils import timezone
from datetime import timedelta


class CustomUserCreationForm(UserCreationForm):
    """Erweiterte Registrierungsform"""
    
    email = forms.EmailField(
        required=True,
        help_text=_('Erforderlich. Geben Sie eine gültige E-Mail-Adresse ein.')
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text=_('Erforderlich.')
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text=_('Erforderlich.')
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Diese E-Mail-Adresse wird bereits verwendet.'))
        return email


class CustomUserChangeForm(UserChangeForm):
    """Formular für User-Bearbeitung durch Admins"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError(_('Diese E-Mail-Adresse wird bereits verwendet.'))
        return email


class UserProfileForm(forms.ModelForm):
    """Formular für Profil-Bearbeitung"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'address', 'company', 'company_logo', 'profile_image', 'email',
            'notify_on_new_employee', 'notify_on_role_change', 'notify_on_new_task', 'notify_on_new_installation', 'notify_on_maintenance_done'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError(_('Diese E-Mail-Adresse wird bereits verwendet.'))
        return email 

class InvitationForm(forms.ModelForm):
    """Formular für das Erstellen von Mitarbeiter-Einladungen"""
    
    class Meta:
        model = Invitation
        fields = ['email', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-Mail-Adresse des neuen Mitarbeiters'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Nur verfügbare Rollen anzeigen (Admin kann alle erstellen)
        if self.user and not self.user.is_admin:
            self.fields['role'].choices = [
                choice for choice in User.Role.choices 
                if choice[0] != User.Role.ADMIN
            ]
    
    def save(self, commit=True):
        invitation = super().save(commit=False)
        invitation.created_by = self.user
        invitation.company = self.user.company
        invitation.expires_at = timezone.now() + timedelta(days=7)  # 7 Tage gültig
        
        if commit:
            invitation.save()
        return invitation

class InvitationAcceptForm(forms.ModelForm):
    """Formular für das Annehmen einer Einladung"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Benutzername'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Vorname'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nachname'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Passwort'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Passwort bestätigen'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwörter stimmen nicht überein.')
        
        return password2
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Dieser Benutzername ist bereits vergeben.')
        return username 