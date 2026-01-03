from django.contrib import admin
from .models import Category, User, Quiz, Question

# Register your models here.
admin.site.register(Category)
admin.site.register(Quiz)
admin.site.register(Question)