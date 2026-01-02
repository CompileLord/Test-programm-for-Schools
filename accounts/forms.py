from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username']
        widget = {
            'username': forms.TextInput(attrs={'class': 'form-register-input', 'placeholder': 'Username'}),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['password1'].widget.attrs.update({'class': 'form-register-input'})
            self.fields['password2'].widget.attrs.update({'class': 'form-register-input'})