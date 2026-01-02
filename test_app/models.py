from django.db import models

# Create your models here.
class Quiz(models.Model):
    title = models.CharField('Name of test', max_length=100)