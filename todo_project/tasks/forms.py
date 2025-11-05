from django import forms
from .models import Task
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Form for creating a user
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'complete']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title'}),
            'complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if self.user and Task.objects.filter(user=self.user, title=title).exists():
            raise forms.ValidationError(f'You already have a task titled "{title}".')
        return title
class SearchForm(forms.Form):
    search=forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Search tasks...'}))
