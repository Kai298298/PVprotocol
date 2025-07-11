"""
URL configuration for pv_protocol project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('installations/', include('installations.urls')),
    path('protocols/', include('protocols.urls')),
    path('payments/', include('payments.urls')),
    path('learning/', include('learning_center.urls', namespace='learning_center')),
    path('', include('django_prometheus.urls')),
    path('', RedirectView.as_view(url='/installations/', permanent=False)),
    path('impressum/', TemplateView.as_view(template_name='base/impressum.html'), name='impressum'),
    path('datenschutz/', TemplateView.as_view(template_name='base/datenschutz.html'), name='datenschutz'),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
