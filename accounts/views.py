from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import User
from .forms import UserRegistrationForm

# Create your views here.
class UserCreationView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')

