from django.urls import path
from django.http import HttpResponse

app_name = 'payments'

def dummy_view(request):
    return HttpResponse('<h1>Demo-Seite</h1><p>Hier kommt später die Abonnementverwaltung.</p>', content_type='text/html; charset=utf-8')

urlpatterns = [
    path('subscriptions/', dummy_view, name='subscription_list'),
] 