from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from .forms import *
from .models import *
from django.db import transaction

# Sign-up form (from lecture notes)
class UserSignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_admin = False
        user.save()
        return user

# Styled login form
class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Your username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Your password'}))

# Update profile picture form
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_pic']

from django import forms
from .models import Feedback

# Feedback input form
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'feedback_type',
            'llm_prompt',
            'llm_response',
            'description',
            'rating',
            'screenshot',
            'transcript',
        ]

class OrganisationCreateForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name']

class OrganisationJoinForm(forms.Form):
    code = forms.CharField(max_length=12, label="Organisation Invite Code")