from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User,Profile,Activity


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username']

class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields=['bio','image']
        widgets={
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write something about yourself'
            }),
        }

class ActivityForm(forms.ModelForm):
    class Meta:
        model=Activity
        fields=['title','description','date'] 
        widgets={
            'title': forms.TextInput(attrs={'placeholder': 'Activity Title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Activity Description'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }