from django.urls import path
from .views import (
    MainPageView, CreateQuizView, QuestionCreateView, QuizDetailView
)

urlpatterns = [
    path('', MainPageView.as_view(), name='main'),
    path('create/', CreateQuizView.as_view(), name='quiz_create'),
    path('quiz/<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('quiz/<int:pk>/add_question/', QuestionCreateView.as_view(), name='add_question'),
]