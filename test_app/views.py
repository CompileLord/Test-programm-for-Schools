from django.http import Http404
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
from django.contrib.auth.models import User
from .forms import QuizForm, QuestionForm, ChoiceFormSet, ChoiceUpdateFormSet

class MainPageView(ListView):
    model = Quiz
    template_name = 'main.html'
    context_object_name = 'quizes'

    def get_queryset(self):
        db_alias = 'default'
        try:
            Quiz.objects.using('online').exists()
            db_alias = 'online'
        except Exception as e:
            print(f"Online DB not available: {e}")
            db_alias = 'default'
        queryset = Quiz.objects.using(db_alias).all()
        
        category = self.request.GET.get('category')
        query = self.request.GET.get('q')
        sort = self.request.GET.get('sort')
        
        if category:
            queryset = queryset.filter(category_id=category)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        if sort == 'asc':
            queryset = queryset.order_by('date_created')
        else:
            queryset = queryset.order_by('-date_created')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_online = self.get_queryset()._db == 'online'
        db_alias = 'online' if is_online else 'default'
        context['categories'] = Category.objects.using(db_alias).all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['is_online_mode'] = is_online
        
        return context
    

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
        # Local attempts
        local_attempts = list(TestAttempt.objects.filter(user=self.request.user))
        
        # Online attempts
        online_attempts = []
        try:
            online_user = User.objects.using('online').filter(username=self.request.user.username).first()
            if online_user:
                online_attempts = list(TestAttempt.objects.using('online').filter(user=online_user))
        except Exception:
            pass
            
        # Combine and sort
        all_attempts = local_attempts + online_attempts
        all_attempts.sort(key=lambda x: x.date_taken, reverse=True)
        return all_attempts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curr_user = self.request.user
        
        local_count = TestAttempt.objects.filter(user=curr_user).count()
        online_count = 0
        try:
            online_user = User.objects.using('online').filter(username=curr_user.username).first()
            if online_user:
                online_count = TestAttempt.objects.using('online').filter(user=online_user).count()
        except Exception:
            pass
            
        context['count_test'] = {'id__count': local_count + online_count}
        return context

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile.html'
    def get_object(self, queryset=None):
        return self.request.user


class PublishQuizView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)

        online_user, created = User.objects.using('online').get_or_create(
            username=request.user.username,
            defaults={
                'email': request.user.email,
                'password': request.user.password 
            }
        )
        online_category, _ = Category.objects.using('online').get_or_create(
            title=quiz.category.title,
            defaults={'image': quiz.category.image}
        )

        try:
            online_quiz = Quiz.objects.using('online').create(
                title=quiz.title,
                user=online_user,
                description=quiz.description,
                category=online_category,
                public=True, 
                date_created=quiz.date_created
            )

            for q in quiz.questions.all():
                online_q = Question.objects.using('online').create(
                    quiz=online_quiz, 
                    text=q.text
                )
                for c in q.choices.all():
                    Choice.objects.using('online').create(
                        question=online_q, 
                        text=c.text, 
                        is_correct=c.is_correct
                    )
            
            quiz.public = True
            quiz.save()
            print(f"Успешно опубликовано в Supabase: {quiz.title}")
            
        except Exception as e:
            print(f"Ошибка при публикации в облако: {e}")

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
    def get(self, request, *args, **kwargs):
        if not Category.objects.exists():
            try:
                online_categories = Category.objects.using('online').all()
                for cat in online_categories:
                    Category.objects.create(
                        title=cat.title,
                        image=cat.image
                    )
            except Exception:
                pass
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class UpdateQuizView(LoginRequiredMixin, UpdateView):
    model = Quiz
    template_name = 'quiz_create.html'
    form_class = QuizForm
    success_url = reverse_lazy('my_quizes')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update'] = True
        return context

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


class UpdateQuestionView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'question_create_form.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['choices'] = ChoiceUpdateFormSet(self.request.POST, instance=self.object)
        else:
            data['choices'] = ChoiceUpdateFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        choices = context['choices']
        if choices.is_valid():
            self.object = form.save()
            choices.instance = self.object
            choices.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('quiz_detail', kwargs={'pk': self.object.quiz.pk})

class DeleteQuestionView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = 'delete_confirm.html'
    
    def get_success_url(self):
        return reverse_lazy('quiz_detail', kwargs={'pk': self.object.quiz.pk})

class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz_detail_view.html'
    context_object_name = 'quiz'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        quiz = Quiz.objects.filter(pk=pk).first()
        if quiz:
            return quiz
        try:
            quiz = Quiz.objects.using('online').filter(pk=pk).first()
            if quiz:
                return quiz
        except Exception:
            pass
            
        raise Http404("No quiz found matching the query")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object
        context['is_owner'] = self.request.user.is_authenticated and quiz.user.username == self.request.user.username
        context['can_take_test'] = (
            self.request.user.is_authenticated and 
            quiz.questions.using(quiz._state.db).exists()
        )
        context['is_online'] = quiz._state.db == 'online'
        return context


class TakeQuizView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'take_quiz.html'
    context_object_name = 'quiz'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        quiz = Quiz.objects.filter(pk=pk).first()
        if not quiz:
            try:
                quiz = Quiz.objects.using('online').filter(pk=pk).first()
            except Exception:
                pass
        if not quiz:
            raise Http404("No quiz found matching the query")
        return quiz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        db_alias = self.object._state.db
        context['questions'] = self.object.questions.using(db_alias).prefetch_related('choices').all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        quiz = self.object
        db_alias = quiz._state.db
        questions = quiz.questions.using(db_alias).prefetch_related('choices').all()
        
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

        # Ensure user exists in the target database
        target_user = request.user
        if db_alias == 'online':
            target_user, _ = User.objects.using('online').get_or_create(
                username=request.user.username,
                defaults={
                    'email': request.user.email,
                    'password': request.user.password
                }
            )

        attempt = TestAttempt.objects.using(db_alias).create(
            user=target_user,
            quiz=quiz,
            score=score,
            total_questions=total
        )

        request.session[f'quiz_result_{attempt.id}'] = {
            'user_answers': {str(k): {'selected_id': v['selected'].id if v['selected'] else None, 'is_correct': v['is_correct']} for k, v in user_answers.items()},
            'db': db_alias
        }

        return redirect('quiz_results', pk=attempt.id)


class QuizResultsView(LoginRequiredMixin, DetailView):
    model = TestAttempt
    template_name = 'quiz_results.html'
    context_object_name = 'attempt'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        # Try local DB
        attempt = TestAttempt.objects.filter(pk=pk, user=self.request.user).first()
        if attempt:
            return attempt
        
        # Try online DB
        try:
            # We need to find the online user first
            online_user = User.objects.using('online').filter(username=self.request.user.username).first()
            if online_user:
                attempt = TestAttempt.objects.using('online').filter(pk=pk, user=online_user).first()
                if attempt:
                    return attempt
        except Exception:
            pass
            
        raise Http404("No attempt found matching the query")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt = self.object
        quiz = attempt.quiz
        
        # If quiz not found locally, try online
        if not Quiz.objects.filter(pk=quiz.pk).exists():
            try:
                online_quiz = Quiz.objects.using('online').filter(pk=quiz.pk).first()
                if online_quiz:
                    quiz = online_quiz
            except Exception:
                pass

        db_alias = quiz._state.db
        questions = quiz.questions.using(db_alias).prefetch_related('choices').all()

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

class ExploreView(ListView):
    model = Category
    template_name = 'explore.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.prefetch_related('quiz_set').all()

