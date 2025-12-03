# masters/forms.py
from django import forms
from .models import Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "head"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Department",
            }),
            "head": forms.Select(attrs={
                "class": "form-select",
            }),
        }