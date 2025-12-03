# masters/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.master_dashboard, name="master_dashboard"),

    # Department Master
    path("departments/", views.department_master, name="department_master"),
    path("departments/<int:pk>/", views.department_master, name="department_edit"),
    path("employee-master/", views.employee_master, name="employee_master"),
]