from django import forms
from django.forms import inlineformset_factory
from .models import Question, Quiz, Choice

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'category','description', 'public']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

ChoiceFormSet = inlineformset_factory(
    Question, Choice,
    fields=['text', 'is_correct'],
    extra=4,
    can_delete=False
)
