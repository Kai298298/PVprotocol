from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, ListView, DeleteView
from .forms import CustomUserCreationForm, CustomUserChangeForm, InvitationForm, InvitationAcceptForm
from .models import User, Invitation
from .forms import UserProfileForm
from protocols.models import Task
from installations.models import PVInstallation
import logging
logger = logging.getLogger('django.security')
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.http import Http404
from django.utils import timezone


class RegisterView(CreateView):
    """Registrierungs-View"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registrierung erfolgreich! Sie können sich jetzt anmelden.')
        logger.info(f"Neuer Benutzer registriert: {form.instance.username} (ID: {form.instance.id}, IP: {self.request.META.get('REMOTE_ADDR')})")
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    """Profil-View"""
    model = User
    template_name = 'accounts/profile.html'
    
    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            context['users'] = User.objects.all().order_by('username')
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Profil-Bearbeitungs-View"""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil erfolgreich aktualisiert!')
        logger.info(f"Profil geändert: User {self.request.user.username} (ID: {self.request.user.id}, IP: {self.request.META.get('REMOTE_ADDR')})")
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard/Landingpage für die SaaS-App. Hier werden die Vorteile und Features beworben.
    """
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Eigene Aufgaben
        my_tasks = Task.objects.filter(assigned_users=user).order_by('-created_at')[:5]
        # Alle Anlagen (Plants)
        plants = PVInstallation.objects.all()[:8]
        # Dummy-Daten für Chart
        chart_data = {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'values': [3, 4, 2, 5, 3, 4, 2],
        }
        context.update({
            'my_tasks': my_tasks,
            'plants': plants,
            'chart_data': chart_data,
        })
        return context


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profil erfolgreich aktualisiert!')
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    def test_func(self):
        return self.request.user.is_admin
    def get_queryset(self):
        return User.objects.filter(company=self.request.user.company)

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    def test_func(self):
        return self.request.user.is_admin
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    def test_func(self):
        return self.request.user.is_admin or self.request.user.pk == self.get_object().pk
    def get_queryset(self):
        return User.objects.filter(company=self.request.user.company)

# Beispiel: E-Mail-Benachrichtigung bei neuer Aufgabe

def notify_new_task(task):
    users = User.objects.filter(company=task.installation.company, notify_on_new_task=True, is_active=True)
    for user in users:
        send_mail(
            subject='Neue Aufgabe zugewiesen',
            message=f'Hallo {user.get_full_name()},\n\nIhnen wurde eine neue Aufgabe zugewiesen: {task.title}.',
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )

# Beispiel: E-Mail-Benachrichtigung bei neuer Anlage

def notify_new_installation(installation):
    users = User.objects.filter(company=installation.company, notify_on_new_installation=True, is_active=True)
    for user in users:
        send_mail(
            subject='Neue Anlage angelegt',
            message=f'Hallo {user.get_full_name()},\n\nEs wurde eine neue Anlage angelegt: {installation.name}.',
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )

# Beispiel: E-Mail-Benachrichtigung bei abgeschlossener Wartung

def notify_maintenance_done(installation):
    users = User.objects.filter(company=installation.company, notify_on_maintenance_done=True, is_active=True)
    for user in users:
        send_mail(
            subject='Wartung abgeschlossen',
            message=f'Hallo {user.get_full_name()},\n\nDie Wartung für die Anlage {installation.name} wurde abgeschlossen.',
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )

@login_required
def invite_employee(request):
    """View für das Erstellen von Mitarbeiter-Einladungen"""
    if request.method == 'POST':
        form = InvitationForm(request.POST, user=request.user)
        if form.is_valid():
            invitation = form.save()
            
            # E-Mail mit Einladungslink senden
            try:
                send_invitation_email(invitation, request)
                messages.success(request, f'Einladung wurde an {invitation.email} gesendet.')
            except Exception as e:
                messages.error(request, f'Fehler beim Senden der E-Mail: {e}')
                invitation.delete()  # Einladung löschen wenn E-Mail fehlschlägt
                return redirect('accounts:user_list')
            
            return redirect('accounts:user_list')
    else:
        form = InvitationForm(user=request.user)
    
    return render(request, 'accounts/invite_employee.html', {
        'form': form,
        'title': 'Mitarbeiter einladen'
    })

def accept_invitation(request, token):
    """View für das Annehmen einer Einladung"""
    invitation = get_object_or_404(Invitation, token=token)
    
    # Prüfe ob Einladung gültig ist
    if not invitation.is_valid():
        if invitation.is_used:
            messages.error(request, 'Diese Einladung wurde bereits verwendet.')
        elif invitation.is_expired():
            messages.error(request, 'Diese Einladung ist abgelaufen.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = InvitationAcceptForm(request.POST)
        if form.is_valid():
            # Neuen User erstellen
            user = form.save(commit=False)
            user.email = invitation.email
            user.role = invitation.role
            user.company = invitation.company
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Einladung als verwendet markieren
            invitation.is_used = True
            invitation.save()
            
            # User automatisch einloggen
            login(request, user)
            messages.success(request, 'Willkommen! Ihr Account wurde erfolgreich erstellt.')
            return redirect('accounts:dashboard')
    else:
        form = InvitationAcceptForm(initial={'email': invitation.email})
    
    return render(request, 'accounts/accept_invitation.html', {
        'form': form,
        'invitation': invitation,
        'title': 'Einladung annehmen'
    })

def send_invitation_email(invitation, request):
    """Sendet E-Mail mit Einladungslink"""
    subject = 'Einladung zum PV-Protokoll System'
    
    # HTML-E-Mail Template
    html_message = render_to_string('accounts/email/invitation.html', {
        'invitation': invitation,
        'invitation_url': invitation.get_invitation_url(request),
        'company_name': invitation.company.name,
        'expires_at': invitation.expires_at.strftime('%d.%m.%Y %H:%M')
    })
    
    # Plain-Text Version
    plain_message = strip_tags(html_message)
    
    # E-Mail senden
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        html_message=html_message,
        fail_silently=False
    )

@login_required
def invitation_list(request):
    """View für die Liste aller Einladungen"""
    invitations = Invitation.objects.filter(
        company=request.user.company
    ).order_by('-created_at')
    
    return render(request, 'accounts/invitation_list.html', {
        'invitations': invitations,
        'title': 'Einladungen'
    })

@login_required
def cancel_invitation(request, pk):
    """View für das Stornieren einer Einladung"""
    invitation = get_object_or_404(Invitation, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        invitation.delete()
        messages.success(request, 'Einladung wurde storniert.')
        return redirect('accounts:invitation_list')
    
    return render(request, 'accounts/cancel_invitation.html', {
        'invitation': invitation,
        'title': 'Einladung stornieren'
    })
