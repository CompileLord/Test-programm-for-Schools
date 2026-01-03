from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View
)
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Sum, Q
from .models import Quiz, Question, TestAttempt, Category, Choice
from django.contrib.auth.models import User as AuthUser
from .forms import QuizForm, QuestionForm, ChoiceFormSet

class MainPageView(ListView):
    model = Quiz
    template_name = 'main.html'
    context_object_name = 'quizes'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        if self.request.user.is_authenticated:
            context['user_tests'] = Quiz.objects.filter(user=self.request.user).order_by('-date_created')
        try:
            Quiz.objects.using('online').only('description').first()
            context['online_tests'] = Quiz.objects.using('online').all()
        except Exception:
            context['online_tests'] = {}
        return context
    def get_queryset(self):
        try:
            Quiz.objects.using('online').only('description').first()
            queryset = Quiz.objects.using('online').all()
        except Exception:
            queryset = Quiz.objects.all()
        
        category = self.request.GET.get('category')
        query = self.request.GET.get('q')
        sort = self.request.GET.get('sort')
        
        if category:
            queryset = queryset.filter(category=category)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        if sort == 'asc':
            queryset = queryset.order_by('-date_created')
        elif sort == 'desc':
            queryset = queryset.order_by('date_created')
        return queryset
    

class MyQuizesView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'my_quizes.html'
    context_object_name = 'quizes'

    def get_queryset(self):
        queryset = Quiz.objects.filter(user=self.request.user).order_by('-date_created')
        
        query = self.request.GET.get('q')
        category_id = self.request.GET.get('category')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category')
        context['search_query'] = self.request.GET.get('q', '')
        return context

class MyHistoryView(LoginRequiredMixin, ListView):
    model = TestAttempt
    template_name = 'my_history.html'
    context_object_name = 'history'
    def get_queryset(self):
        queryset = TestAttempt.objects.filter(user=self.request.user)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curr_user = self.request.user
        context['count_test'] = TestAttempt.objects.filter(user=curr_user).aggregate(Count('id'))
        return context


class PublishQuizView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)

        online_user = AuthUser.objects.using('online').filter(username=request.user.username).first()
        if not online_user:
            online_user = AuthUser.objects.using('online').first()
        if not online_user:
            return redirect('my_quizes')

        # Ensure category exists on online DB (use same title and image path)
        online_category, _ = Category.objects.using('online').get_or_create(
            title=quiz.category.title,
            defaults={'image': quiz.category.image}
        )

        # Create the quiz on the online DB
        online_quiz = Quiz.objects.using('online').create(
            title=quiz.title,
            user=online_user,
            description=quiz.description,
            category=online_category,
            public=True,
            date_created=quiz.date_created
        )

        # Copy questions and choices
        for q in quiz.questions.all():
            online_q = Question.objects.using('online').create(quiz=online_quiz, text=q.text)
            for c in q.choices.all():
                Choice.objects.using('online').create(question=online_q, text=c.text, is_correct=c.is_correct)

        # Mark original as public and return
        quiz.public = True
        quiz.save()
        return redirect('my_quizes')


class DeleteQuiz(LoginRequiredMixin, DeleteView):
    model = Quiz
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('main')
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


    

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

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['choices'] = ChoiceFormSet(self.request.POST)
        else:
            data['choices'] = ChoiceFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        choices = context['choices']
        quiz = get_object_or_404(Quiz, pk=self.kwargs['pk'])
        form.instance.quiz = quiz
        if choices.is_valid():
            self.object = form.save()
            choices.instance = self.object
            choices.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('add_question', kwargs={'pk': self.kwargs['pk']})


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz_detail_view.html'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_owner'] = self.request.user == self.object.user
        context['can_take_test'] = (
            self.request.user.is_authenticated and 
            self.object.questions.exists()
        )
        return context


class TakeQuizView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'take_quiz.html'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.prefetch_related('choices').all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        quiz = self.object
        questions = quiz.questions.prefetch_related('choices').all()
        
        score = 0
        total = questions.count()
        user_answers = {}

        for question in questions:
            answer_key = f'question_{question.id}'
            selected_choice_id = request.POST.get(answer_key)
            
            if selected_choice_id:
                try:
                    selected_choice = question.choices.get(id=selected_choice_id)
                    user_answers[question.id] = {
                        'selected': selected_choice,
                        'is_correct': selected_choice.is_correct
                    }
                    if selected_choice.is_correct:
                        score += 1
                except:
                    user_answers[question.id] = {'selected': None, 'is_correct': False}
            else:
                user_answers[question.id] = {'selected': None, 'is_correct': False}

        attempt = TestAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            total_questions=total
        )

        request.session[f'quiz_result_{attempt.id}'] = {
            'user_answers': {str(k): {'selected_id': v['selected'].id if v['selected'] else None, 'is_correct': v['is_correct']} for k, v in user_answers.items()}
        }

        return redirect('quiz_results', pk=attempt.id)


class QuizResultsView(LoginRequiredMixin, DetailView):
    model = TestAttempt
    template_name = 'quiz_results.html'
    context_object_name = 'attempt'

    def get_queryset(self):
        return TestAttempt.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        quiz = attempt.quiz
        questions = quiz.questions.prefetch_related('choices').all()

        session_key = f'quiz_result_{attempt.id}'
        session_data = self.request.session.get(session_key, {})
        user_answers_data = session_data.get('user_answers', {})

        results = []
        for question in questions:
            answer_data = user_answers_data.get(str(question.id), {})
            selected_id = answer_data.get('selected_id')
            is_correct = answer_data.get('is_correct', False)
            
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = None
            if selected_id:
                try:
                    selected_choice = question.choices.get(id=selected_id)
                except:
                    pass

            results.append({
                'question': question,
                'selected': selected_choice,
                'correct': correct_choice,
                'is_correct': is_correct
            })

        context['results'] = results
        context['quiz'] = quiz
        return context
