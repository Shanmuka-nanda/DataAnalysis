from django import forms
from django.core.exceptions import ValidationError
from .models import Project
import os

class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'dataset']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Project Name', 'class': 'form-input'}),
            'description': forms.Textarea(attrs={'placeholder': 'Brief description...', 'class': 'form-input', 'rows': 4}),
            'dataset': forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv,.xlsx', 'required': 'required'})
        }

    def clean_dataset(self):
        dataset = self.cleaned_data.get('dataset')
        if dataset:
            ext = os.path.splitext(dataset.name)[1].lower()
            if ext not in ['.csv', '.xlsx']:
                raise ValidationError('Unsupported file extension. Only .csv and .xlsx allowed.')
            if dataset.size > 200 * 1024 * 1024:
                raise ValidationError('File too large. Size should not exceed 200 MB.')
        return dataset