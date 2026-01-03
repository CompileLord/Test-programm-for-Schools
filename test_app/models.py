from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/')
    def __str__(self):
        return self.title

class Quiz(models.Model):
    title = models.CharField('Name of test', max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('quiz_detail', args=[str(self.id)])

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Text of question', max_length=100)

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField('Variant of answer', max_length=100)
    is_correct = models.BooleanField('Is this the correct variant?', default=False)

class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    date_taken = models.DateTimeField(auto_now_add=True)

    def get_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100)

    class Meta:
        ordering = ['-date_taken']