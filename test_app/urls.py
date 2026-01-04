from django.urls import path
from .views import (
    MainPageView, CreateQuizView, QuestionCreateView, QuizDetailView,
    TakeQuizView, QuizResultsView, MyQuizesView, DeleteQuiz, MyHistoryView,
    PublishQuizView, ProfileView, ExploreView, UpdateQuizView,
    UpdateQuestionView, DeleteQuestionView
)

urlpatterns = [
    path('', MainPageView.as_view(), name='main'),
    path('explore/', ExploreView.as_view(), name='explore'),
    path('create/', CreateQuizView.as_view(), name='quiz_create'),
    path('quiz/<int:pk>/update/', UpdateQuizView.as_view(), name='update_quiz'),
    path('my-quizes/', MyQuizesView.as_view(), name='my_quizes'),
    path('my_history/', MyHistoryView.as_view(), name='my_history'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('quiz/<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('quiz/<int:pk>/add_question/', QuestionCreateView.as_view(), name='add_question'),
    path('question/<int:pk>/update/', UpdateQuestionView.as_view(), name='update_question'),
    path('question/<int:pk>/delete/', DeleteQuestionView.as_view(), name='delete_question'),
    path('quiz/<int:pk>/take/', TakeQuizView.as_view(), name='take_quiz'),
    path('quiz/<int:pk>/delete/', DeleteQuiz.as_view(), name='delete_quiz'),
    path('quiz/<int:pk>/publish/', PublishQuizView.as_view(), name='publish_quiz'),
    path('results/<int:pk>/', QuizResultsView.as_view(), name='quiz_results'),
]