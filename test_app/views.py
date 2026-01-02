from django.shortcuts import get_object_or_404
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Quiz, Question
from .forms import QuizForm, QuestionForm

# Create your views here.

class MainPageView(ListView):
    model = Quiz
    template_name = 'main'
    context_object_name = 'quizes'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_tests'] = Quiz.objects.filter(user=self.request.user).order_by('-date_created')
        return context

class CreateQuizView(LoginRequiredMixin, CreateView):
    model = Quiz
    template_name = 'quiz_create.html'
    form_class = QuizForm
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'question_create_form.html'
    def form_valid(self, valid):
        quiz_id = self.kwargs['pk']
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        form.instance.quiz = quiz
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('quiz_detail.html', kwargs={'pk':self.kwargs['pk']})

class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz_detail_view.html'
    context_object_name = 'quiz'

        