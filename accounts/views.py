from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from .models import User
from .forms import UserRegistrationForm

# Create your views here.
class UserCreationView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')

def logout_view(request):
    logout(request)
    return redirect('main')
