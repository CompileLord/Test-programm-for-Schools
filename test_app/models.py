from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
# Create your models here.
class Quiz(models.Model):
    title = models.CharField('Name of test', max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('quiz_detail', args=[str(self.id)])

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Text of question', max_length=100)
    correct_answer = models.CharField('Correct answer', max_length=100)
        