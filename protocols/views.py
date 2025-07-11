from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import Task, TaskNote, TaskImage, Protocol, ProtocolTemplate
from .forms import TaskForm, TaskNoteForm, TaskFilterForm, TaskBulkActionForm, ProtocolTemplateForm
from installations.models import PVInstallation
from accounts.models import User

# === AUFGABENVERWALTUNG ===

class TaskListView(LoginRequiredMixin, ListView):
    """Moderne Aufgabenliste mit Filterung, Suche und Bulk-Aktionen"""
    model = Task
    template_name = 'protocols/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        """Erweiterte Queryset mit Filterung und Suche"""
        queryset = Task.objects.select_related(
            'installation', 'created_by', 'company'
        ).prefetch_related(
            'assigned_users', 'notes', 'images'
        )
        
        # Mandantenfähigkeit
        if not self.request.user.is_superuser:
            queryset = queryset.filter(company=self.request.user.company)
        
        # Filterung
        form = TaskFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            # Suche
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(tags__icontains=search)
                )
            
            # Status-Filter
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            # Prioritäts-Filter
            priority = form.cleaned_data.get('priority')
            if priority:
                queryset = queryset.filter(priority=priority)
            
            # Zugewiesener Mitarbeiter
            assigned_to = form.cleaned_data.get('assigned_to')
            if assigned_to:
                queryset = queryset.filter(assigned_users=assigned_to)
            
            # Anlagen-Filter
            installation = form.cleaned_data.get('installation')
            if installation:
                queryset = queryset.filter(installation=installation)
            
            # Datums-Filter
            due_date_from = form.cleaned_data.get('due_date_from')
            if due_date_from:
                queryset = queryset.filter(due_date__date__gte=due_date_from)
            
            due_date_to = form.cleaned_data.get('due_date_to')
            if due_date_to:
                queryset = queryset.filter(due_date__date__lte=due_date_to)
            
            # Nur überfällige Aufgaben
            if form.cleaned_data.get('overdue_only'):
                queryset = queryset.filter(
                    due_date__lt=timezone.now(),
                    status__in=[Task.TaskStatus.TODO, Task.TaskStatus.IN_PROGRESS, Task.TaskStatus.REVIEW]
                )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter-Formular
        context['filter_form'] = TaskFilterForm(self.request.GET, user=self.request.user)
        
        # Statistiken
        queryset = self.get_queryset()
        context['stats'] = {
            'total': queryset.count(),
            'todo': queryset.filter(status=Task.TaskStatus.TODO).count(),
            'in_progress': queryset.filter(status=Task.TaskStatus.IN_PROGRESS).count(),
            'completed': queryset.filter(status=Task.TaskStatus.COMPLETED).count(),
            'overdue': queryset.filter(
                due_date__lt=timezone.now(),
                status__in=[Task.TaskStatus.TODO, Task.TaskStatus.IN_PROGRESS, Task.TaskStatus.REVIEW]
            ).count(),
        }
        
        # Bulk-Action-Formular
        context['bulk_form'] = TaskBulkActionForm()
        
        return context

class TaskDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detaillierte Aufgabenansicht mit Notizen und Aktionen"""
    model = Task
    template_name = 'protocols/task_detail.html'
    context_object_name = 'task'
    
    def test_func(self):
        """Berechtigungsprüfung"""
        task = self.get_object()
        user = self.request.user
        
        # Superuser oder zugeordneter Mitarbeiter
        return user.is_superuser or user in task.assigned_users.all() or user == task.created_by
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Notizen-Formular
        context['note_form'] = TaskNoteForm()
        
        # Notizen des Tasks
        context['notes'] = self.object.notes.select_related('author').order_by('-created_at')
        
        # Ähnliche Aufgaben
        context['similar_tasks'] = Task.objects.filter(
            installation=self.object.installation
        ).exclude(id=self.object.id)[:5]
        
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    """Aufgabe erstellen mit erweiterten Features"""
    model = Task
    form_class = TaskForm
    template_name = 'protocols/task_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.company = self.request.user.company
        
        response = super().form_valid(form)
        messages.success(self.request, 'Aufgabe erfolgreich erstellt.')
        return response
    
    def get_success_url(self):
        return reverse('protocols:task_detail', kwargs={'pk': self.object.pk})

class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Aufgabe bearbeiten"""
    model = Task
    form_class = TaskForm
    template_name = 'protocols/task_form.html'
    
    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return user.is_superuser or user in task.assigned_users.all() or user == task.created_by
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Aufgabe erfolgreich aktualisiert.')
        return response
    
    def get_success_url(self):
        return reverse('protocols:task_detail', kwargs={'pk': self.object.pk})

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Aufgabe löschen"""
    model = Task
    template_name = 'protocols/task_confirm_delete.html'
    success_url = reverse_lazy('protocols:task_list')
    
    def test_func(self):
        task = self.get_object()
        user = self.request.user
        return user.is_superuser or user == task.created_by
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Aufgabe erfolgreich gelöscht.')
        return super().delete(request, *args, **kwargs)

# === NOTIZEN-VIEWS ===

@login_required
@require_POST
def add_task_note(request, task_id):
    """Notiz zu einer Aufgabe hinzufügen"""
    task = get_object_or_404(Task, id=task_id)
    
    # Berechtigungsprüfung
    if not (request.user.is_superuser or 
            request.user in task.assigned_users.all() or 
            request.user == task.created_by):
        messages.error(request, 'Keine Berechtigung für diese Aktion.')
        return redirect('protocols:task_detail', pk=task_id)
    
    form = TaskNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.task = task
        note.author = request.user
        note.save()
        
        messages.success(request, 'Notiz erfolgreich hinzugefügt.')
    else:
        messages.error(request, 'Fehler beim Hinzufügen der Notiz.')
    
    return redirect('protocols:task_detail', pk=task_id)

@login_required
@require_POST
def delete_task_note(request, note_id):
    """Notiz löschen"""
    note = get_object_or_404(TaskNote, id=note_id)
    
    # Berechtigungsprüfung
    if not (request.user.is_superuser or request.user == note.author):
        messages.error(request, 'Keine Berechtigung für diese Aktion.')
        return redirect('protocols:task_detail', pk=note.task.id)
    
    task_id = note.task.id
    note.delete()
    messages.success(request, 'Notiz erfolgreich gelöscht.')
    
    return redirect('protocols:task_detail', pk=task_id)

# === BULK-AKTIONEN ===

@login_required
@require_POST
def bulk_action_tasks(request):
    """Bulk-Aktionen auf Aufgaben ausführen"""
    form = TaskBulkActionForm(request.POST)
    
    if form.is_valid():
        action = form.cleaned_data['action']
        task_ids = form.cleaned_data['task_ids'].split(',')
        tasks = Task.objects.filter(id__in=task_ids)
        
        # Berechtigungsprüfung
        if not request.user.is_superuser:
            tasks = tasks.filter(company=request.user.company)
        
        if action == 'start':
            for task in tasks:
                task.start_task()
            messages.success(request, f'{tasks.count()} Aufgaben gestartet.')
        
        elif action == 'complete':
            for task in tasks:
                task.complete_task()
            messages.success(request, f'{tasks.count()} Aufgaben abgeschlossen.')
        
        elif action == 'assign':
            assign_to = form.cleaned_data['assign_to']
            for task in tasks:
                task.assigned_users.set(assign_to)
            messages.success(request, f'Mitarbeiter für {tasks.count()} Aufgaben zugewiesen.')
        
        elif action == 'change_status':
            new_status = form.cleaned_data['new_status']
            tasks.update(status=new_status)
            messages.success(request, f'Status für {tasks.count()} Aufgaben geändert.')
        
        elif action == 'change_priority':
            new_priority = form.cleaned_data['new_priority']
            tasks.update(priority=new_priority)
            messages.success(request, f'Priorität für {tasks.count()} Aufgaben geändert.')
        
        elif action == 'delete':
            count = tasks.count()
            tasks.delete()
            messages.success(request, f'{count} Aufgaben gelöscht.')
    
    return redirect('protocols:task_list')

# === AJAX-VIEWS ===

@login_required
def task_status_update(request, task_id):
    """Status einer Aufgabe per AJAX aktualisieren"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        
        # Berechtigungsprüfung
        if not (request.user.is_superuser or 
                request.user in task.assigned_users.all() or 
                request.user == task.created_by):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)
        
        new_status = request.POST.get('status')
        if new_status in dict(Task.TaskStatus.choices):
            task.status = new_status
            if new_status == Task.TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = timezone.now()
            elif new_status == Task.TaskStatus.COMPLETED:
                task.completed_at = timezone.now()
            task.save()
            
            return JsonResponse({
                'success': True,
                'status': new_status,
                'status_display': dict(Task.TaskStatus.choices)[new_status],
                'progress': task.get_progress_percentage()
            })
    
    return JsonResponse({'error': 'Ungültige Anfrage'}, status=400)

@login_required
def task_progress_chart(request):
    """Daten für Fortschritts-Chart"""
    if not request.user.is_superuser:
        tasks = Task.objects.filter(company=request.user.company)
    else:
        tasks = Task.objects.all()
    
    status_counts = tasks.values('status').annotate(count=Count('id'))
    
    chart_data = {
        'labels': [],
        'data': [],
        'colors': []
    }
    
    for item in status_counts:
        status = item['status']
        chart_data['labels'].append(dict(Task.TaskStatus.choices)[status])
        chart_data['data'].append(item['count'])
        chart_data['colors'].append(Task().get_status_color())
    
    return JsonResponse(chart_data)

# === DASHBOARD-VIEWS ===

@login_required
def task_dashboard(request):
    """Dashboard für Aufgabenverwaltung"""
    if not request.user.is_superuser:
        tasks = Task.objects.filter(company=request.user.company)
    else:
        tasks = Task.objects.all()
    
    # Statistiken
    stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status=Task.TaskStatus.TODO).count(),
        'in_progress': tasks.filter(status=Task.TaskStatus.IN_PROGRESS).count(),
        'completed': tasks.filter(status=Task.TaskStatus.COMPLETED).count(),
        'overdue': tasks.filter(
            due_date__lt=timezone.now(),
            status__in=[Task.TaskStatus.TODO, Task.TaskStatus.IN_PROGRESS, Task.TaskStatus.REVIEW]
        ).count(),
    }
    
    # Neueste Aufgaben
    recent_tasks = tasks.select_related('installation', 'created_by').order_by('-created_at')[:10]
    
    # Überfällige Aufgaben
    overdue_tasks = tasks.filter(
        due_date__lt=timezone.now(),
        status__in=[Task.TaskStatus.TODO, Task.TaskStatus.IN_PROGRESS, Task.TaskStatus.REVIEW]
    ).select_related('installation', 'created_by')[:5]
    
    # Aufgaben nach Priorität
    priority_stats = tasks.values('priority').annotate(count=Count('id'))
    
    context = {
        'stats': stats,
        'recent_tasks': recent_tasks,
        'overdue_tasks': overdue_tasks,
        'priority_stats': priority_stats,
    }
    
    return render(request, 'protocols/task_dashboard.html', context)

# === PROTOKOLL-VIEWS ===

class ProtocolListView(LoginRequiredMixin, ListView):
    """Protokoll-Liste"""
    model = Protocol
    template_name = 'protocols/protocol_list.html'
    context_object_name = 'protocols'
    paginate_by = 20

class ProtocolCreateView(LoginRequiredMixin, CreateView):
    """Protokoll erstellen"""
    model = Protocol
    template_name = 'protocols/protocol_form.html'
    fields = ['title', 'installation', 'template', 'content']
    success_url = reverse_lazy('protocols:protocol_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ProtocolDetailView(LoginRequiredMixin, DetailView):
    """Protokoll-Details"""
    model = Protocol
    template_name = 'protocols/protocol_detail.html'
    context_object_name = 'protocol'

class ProtocolUpdateView(LoginRequiredMixin, UpdateView):
    """Protokoll bearbeiten"""
    model = Protocol
    template_name = 'protocols/protocol_form.html'
    fields = ['title', 'installation', 'template', 'content', 'status']
    success_url = reverse_lazy('protocols:protocol_list')

class ProtocolDeleteView(LoginRequiredMixin, DeleteView):
    """Protokoll löschen"""
    model = Protocol
    template_name = 'protocols/protocol_confirm_delete.html'
    success_url = reverse_lazy('protocols:protocol_list')

class ProtocolPDFExportView(LoginRequiredMixin, DetailView):
    """PDF-Export für Protokolle"""
    model = Protocol
    template_name = 'protocols/protocol_pdf.html'
    context_object_name = 'protocol'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return render(request, self.template_name, context)

# === VORLAGEN-VIEWS ===

class ProtocolTemplateListView(LoginRequiredMixin, ListView):
    """Vorlagen-Liste"""
    model = ProtocolTemplate
    template_name = 'protocols/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

class ProtocolTemplateCreateView(LoginRequiredMixin, CreateView):
    """Vorlage erstellen"""
    model = ProtocolTemplate
    form_class = ProtocolTemplateForm
    template_name = 'protocols/template_form.html'
    success_url = reverse_lazy('protocols:template_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ProtocolTemplateDetailView(LoginRequiredMixin, DetailView):
    """Vorlagen-Details"""
    model = ProtocolTemplate
    template_name = 'protocols/template_detail.html'
    context_object_name = 'template'

class ProtocolTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Vorlage bearbeiten"""
    model = ProtocolTemplate
    form_class = ProtocolTemplateForm
    template_name = 'protocols/template_form.html'
    success_url = reverse_lazy('protocols:template_list')

class ProtocolTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Vorlage löschen"""
    model = ProtocolTemplate
    template_name = 'protocols/template_confirm_delete.html'
    success_url = reverse_lazy('protocols:template_list')
