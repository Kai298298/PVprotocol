from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, TemplateView
from django.shortcuts import render
from .models import PVInstallation, Customer
from .models import InstallationNote, InstallationMaintenance
from django.urls import reverse_lazy
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.contrib import messages
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
import json

# Dashboard für Anlagenverwaltung
class InstallationDashboardView(LoginRequiredMixin, View):
    """
    Dashboard für Anlagenverwaltung - Übersicht über Kunden und Anlagen
    """
    template_name = 'installations/dashboard.html'
    
    def get(self, request):
        # Statistiken sammeln
        total_customers = Customer.objects.count()
        total_installations = PVInstallation.objects.count()
        installations_without_customer = PVInstallation.objects.filter(operator__isnull=True).count()
        installations_with_customer = PVInstallation.objects.filter(operator__isnull=False).count()
        
        # Neueste Einträge
        recent_customers = Customer.objects.select_related('user').order_by('-created_at')[:5]
        recent_installations = PVInstallation.objects.select_related('operator').order_by('-created_at')[:5]
        
        context = {
            'total_customers': total_customers,
            'total_installations': total_installations,
            'installations_without_customer': installations_without_customer,
            'installations_with_customer': installations_with_customer,
            'recent_customers': recent_customers,
            'recent_installations': recent_installations,
        }
        
        return render(request, self.template_name, context)

# Anlagen-Listenansicht
class InstallationListView(LoginRequiredMixin, ListView):
    """
    Zeigt eine Liste aller PV-Anlagen an, mit Such-/Filterfunktion und Berechtigungslogik.
    """
    model = PVInstallation
    template_name = 'installations/installation_list.html'
    context_object_name = 'installations'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('operator')
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(location__icontains=search) |
                models.Q(module_type__icontains=search) |
                models.Q(module_manufacturer__icontains=search) |
                models.Q(operator__user__first_name__icontains=search) |
                models.Q(operator__user__last_name__icontains=search)
            )
        # SaaS-Logik: Zeige nur Anlagen, die zum User/Mandanten gehören
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(operator__user=user)
        return queryset

# Anlagen-Detailansicht
class InstallationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Zeigt die Detailansicht einer PV-Anlage an, mit Berechtigungsprüfung und CRM-Zeitverlauf.
    """
    model = PVInstallation
    template_name = 'installations/installation_detail.html'
    context_object_name = 'installation'

    def test_func(self):
        user = self.request.user
        installation = self.get_object()
        return user.is_superuser or (installation.operator and installation.operator.user == user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        installation = self.object
        # Notizen
        notes = InstallationNote.objects.filter(installation=installation)
        # Wartungen
        maintenances = InstallationMaintenance.objects.filter(installation=installation)
        # Kombinierter Zeitverlauf
        timeline = []
        for note in notes:
            timeline.append({
                'type': 'note',
                'title': note.title,
                'content': note.content,
                'note_type': note.note_type,
                'created_at': note.created_at,
                'created_by': note.created_by,
                'is_important': note.is_important,
            })
        for maint in maintenances:
            timeline.append({
                'type': 'maintenance',
                'title': maint.title,
                'content': maint.description,
                'maintenance_type': maint.maintenance_type,
                'scheduled_date': maint.scheduled_date,
                'completed_date': maint.completed_date,
                'status': maint.status,
                'technician': maint.technician,
                'notes': maint.notes,
                'created_at': maint.created_at,
                'created_by': maint.created_by,
            })
        # Sortiere nach Zeit absteigend
        timeline.sort(key=lambda x: x['created_at'], reverse=True)
        context['timeline'] = timeline
        return context

class InstallationCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            customers = Customer.objects.filter(user=user)
            if customers.count() == 1:
                self.fields['operator'].initial = customers.first().pk
                self.fields['operator'].widget = forms.HiddenInput()

    class Meta:
        model = PVInstallation
        fields = ['name', 'location', 'module_type', 'module_manufacturer', 'operator', 'size', 'total_power_kw', 'number_of_modules', 'address', 'profile_image']

class InstallationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PVInstallation
    form_class = InstallationCreateForm
    template_name = 'installations/installation_form.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'admin'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        try:
            customer = Customer.objects.get(user=self.request.user)
            initial['operator'] = customer.pk
        except Customer.DoesNotExist:
            pass
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Anlage erfolgreich angelegt.')
        return reverse('installations:installation_list')

# Anlage bearbeiten
class InstallationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PVInstallation
    fields = ['name', 'size', 'location', 'module_type', 'module_manufacturer', 'operator', 'profile_image']
    template_name = 'installations/installation_form.html'
    success_url = reverse_lazy('installations:installation_list')

# Kunden-Listenansicht
class CustomerListView(LoginRequiredMixin, ListView):
    """
    Zeigt eine Liste aller Kunden im System an.
    Die Ansicht nutzt ein modernes, responsives Template mit blauer Akzentfarbe.
    """
    model = Customer
    template_name = 'installations/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Optional: Ermöglicht Suche/Filterung nach Name, Kundennummer oder E-Mail.
        """
        queryset = super().get_queryset().select_related('user')
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(user__email__icontains=search) |
                models.Q(customer_number__icontains=search)
            )
        return queryset

# Kunden-Detailansicht
class CustomerDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Zeigt die Detailansicht eines Kunden an.
    Nur berechtigte Nutzer (Admin, zugeordneter User) dürfen Details sehen.
    """
    model = Customer
    template_name = 'installations/customer_detail.html'
    context_object_name = 'customer'

    def test_func(self):
        # Admins oder der zugeordnete User dürfen Details sehen
        user = self.request.user
        customer = self.get_object()
        return user.is_superuser or user == customer.user

class CustomerCreateForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'address', 'email', 'phone', 'company_name']

class CustomerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Customer
    form_class = CustomerCreateForm
    template_name = 'installations/customer_form.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'admin'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Kunde erfolgreich angelegt.')
        return reverse('installations:customer_list')

# Kunden bearbeiten
class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    fields = ['name', 'address', 'email', 'phone', 'company_name']
    template_name = 'installations/customer_form.html'
    success_url = reverse_lazy('installations:customer_list')

    def test_func(self):
        user = self.request.user
        customer = self.get_object()
        return user.is_superuser or user == customer.user

@require_POST
def add_note(request, pk):
    """Notiz zu einer Anlage hinzufügen"""
    installation = get_object_or_404(PVInstallation, pk=pk)
    
    # Berechtigungsprüfung
    if not request.user.is_superuser and installation.operator and installation.operator.user != request.user:
        messages.error(request, 'Keine Berechtigung für diese Anlage.')
        return redirect('installations:installation_detail', pk=pk)
    
    title = request.POST.get('title')
    content = request.POST.get('content')
    note_type = request.POST.get('note_type', 'general')
    is_important = request.POST.get('is_important') == 'on'
    
    if title and content:
        InstallationNote.objects.create(
            installation=installation,
            title=title,
            content=content,
            note_type=note_type,
            is_important=is_important,
            created_by=request.user
        )
        messages.success(request, 'Notiz erfolgreich hinzugefügt.')
    else:
        messages.error(request, 'Bitte füllen Sie alle Pflichtfelder aus.')
    
    return redirect('installations:installation_detail', pk=pk)

@require_POST
def add_maintenance(request, pk):
    """Wartung zu einer Anlage hinzufügen"""
    installation = get_object_or_404(PVInstallation, pk=pk)
    
    # Berechtigungsprüfung
    if not request.user.is_superuser and installation.operator and installation.operator.user != request.user:
        messages.error(request, 'Keine Berechtigung für diese Anlage.')
        return redirect('installations:installation_detail', pk=pk)
    
    title = request.POST.get('title')
    description = request.POST.get('description')
    maintenance_type = request.POST.get('maintenance_type')
    scheduled_date = request.POST.get('scheduled_date')
    maintenance_notes = request.POST.get('maintenance_notes', '')
    
    if title and description and maintenance_type and scheduled_date:
        InstallationMaintenance.objects.create(
            installation=installation,
            title=title,
            description=description,
            maintenance_type=maintenance_type,
            scheduled_date=scheduled_date,
            maintenance_notes=maintenance_notes,
            created_by=request.user
        )
        messages.success(request, 'Wartung erfolgreich hinzugefügt.')
    else:
        messages.error(request, 'Bitte füllen Sie alle Pflichtfelder aus.')
    
    return redirect('installations:installation_detail', pk=pk)

class InstallationCSVImportView(LoginRequiredMixin, TemplateView):
    template_name = 'installations/installation_csv_import.html'
