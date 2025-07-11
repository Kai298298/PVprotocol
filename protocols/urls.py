from django.urls import path
from . import views

app_name = 'protocols'

urlpatterns = [
    # === AUFGABENVERWALTUNG ===
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/dashboard/', views.task_dashboard, name='task_dashboard'),
    path('tasks/bulk-action/', views.bulk_action_tasks, name='bulk_action_tasks'),
    # === PROTOKOLLE ===
    path('protocols/', views.ProtocolListView.as_view(), name='protocol_list'),
    path('protocols/create/', views.ProtocolCreateView.as_view(), name='protocol_create'),
    path('protocols/<int:pk>/', views.ProtocolDetailView.as_view(), name='protocol_detail'),
    path('protocols/<int:pk>/edit/', views.ProtocolUpdateView.as_view(), name='protocol_update'),
    path('protocols/<int:pk>/delete/', views.ProtocolDeleteView.as_view(), name='protocol_delete'),
    # === VORLAGEN ===
    path('templates/', views.ProtocolTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ProtocolTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.ProtocolTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/edit/', views.ProtocolTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.ProtocolTemplateDeleteView.as_view(), name='template_delete'),
] 