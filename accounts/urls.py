from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import ListView
from .views import DashboardView, RegisterView, ProfileView, ProfileEditView, UserListView, UserCreateView, UserUpdateView
from .models import User
from django.http import HttpResponse
from . import views

app_name = 'accounts'

# UserListView wird direkt aus views.py importiert

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),

    # Einladungssystem
    path('invite/', views.invite_employee, name='invite_employee'),
    path('invite/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    path('invitations/', views.invitation_list, name='invitation_list'),
    path('invitations/<int:pk>/cancel/', views.cancel_invitation, name='cancel_invitation'),
] 