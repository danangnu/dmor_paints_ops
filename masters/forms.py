# masters/forms.py
from django import forms
from .models import Employee, Department

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

class EmployeeForm(forms.ModelForm):
    emp_dob = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    joining_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    class Meta:
        model = Employee
        fields = [
            "employee_id",
            "prefix",
            "first_name",
            "middle_name",
            "last_name",
            "mobile_no",
            "email",
            "emp_dob",
            "emp_type",
            "department",
            "username",
            "joining_date",
            "current_branch",
            "designation",
            "password",
        ]
        widgets = {
            "employee_id": forms.TextInput(attrs={"class": "form-control"}),
            "prefix": forms.Select(
                attrs={"class": "form-select"},
                choices=[("", "Select"), ("Mr", "Mr"), ("Mrs", "Mrs"), ("Ms", "Ms")],
            ),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "mobile_no": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "emp_type": forms.Select(attrs={"class": "form-select"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "current_branch": forms.TextInput(attrs={"class": "form-control"}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
        }