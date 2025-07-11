from django.urls import path
from .views import LearningCenterView, LearningLessonView

app_name = 'learning_center'

urlpatterns = [
    path('', LearningCenterView.as_view(), name='learning_center'),
    path('<slug:slug>/', LearningLessonView.as_view(), name='lesson_detail'),
] 