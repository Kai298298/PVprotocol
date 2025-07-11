from django.urls import path
from django.http import HttpResponse
from django.views.generic import RedirectView
from .views import CustomerListView
from .views import CustomerDetailView
from .views import InstallationListView, InstallationDetailView
from .views import CustomerCreateView, InstallationCreateView
from .views import InstallationDashboardView
from .views import add_note, add_maintenance
from .views import CustomerUpdateView
from .views import InstallationCSVImportView

app_name = 'installations'

urlpatterns = [
    # Haupt-URL für Anlagenverwaltung - Dashboard
    path('', InstallationDashboardView.as_view(), name='installations_dashboard'),
    
    # Kunden-Verwaltung (unabhängig von Anlagen)
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/new/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_update'),
    
    # Anlagen-Verwaltung (unabhängig von Kunden)
    path('installations/', InstallationListView.as_view(), name='installation_list'),
    path('installations/new/', InstallationCreateView.as_view(), name='installation_create'),
    path('installations/<int:pk>/', InstallationDetailView.as_view(), name='installation_detail'),
    path('list/', InstallationListView.as_view(), name='installation_list_explicit'),
    path('installations/import/', InstallationCSVImportView.as_view(), name='installation_csv_import'),
    
    # CRM-Funktionen für Anlagen
    path('installations/<int:pk>/add_note/', add_note, name='add_note'),
    path('installations/<int:pk>/add_maintenance/', add_maintenance, name='add_maintenance'),
] 