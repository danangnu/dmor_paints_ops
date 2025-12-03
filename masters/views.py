# masters/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Department, Employee
from .forms import DepartmentForm, EmployeeForm

def master_dashboard(request):
    tiles_row1 = [
        {
            "title": "Department",
            "icon": "img/master_department.png",
            "url": reverse("department_master"),
        },
        {
            "title": "Designation",
            "icon": "img/master_designation.png",
            "url": "#",
        },
        {
            "title": "Employee Master",
            "icon": "img/master_employee.png",
            "url": reverse("employee_master"),
        },
        {
            "title": "Unit Master",
            "icon": "img/master_unit.png",
            "url": "#",
        },
        {
            "title": "Master Product",
            "icon": "img/master_product.png",
            "url": "#",
        },
        {
            "title": "Product Master",
            "icon": "img/master_product_master.png",
            "url": "#",
        },
    ]

    tiles_row2 = [
        {
            "title": "Terms and Conditions",
            "icon": "img/master_terms.png",
            "url": "#",
        },
        {
            "title": "Add New Customer",
            "icon": "img/master_customer.png",
            "url": "#",
        },
        {
            "title": "Product BOM",
            "icon": "img/master_bom.png",
            "url": "#",
        },
        {
            "title": "Product Development",
            "icon": "img/master_development.png",
            "url": "#",
        },
    ]

    context = {
        "row1": tiles_row1,
        "row2": tiles_row2,
    }
    return render(request, "masters/master_dashboard.html", context)

def department_master(request, pk=None):
    """Department Master screen: create/edit departments."""
    department = None
    if pk is not None:
        department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "close":
            return redirect("master_dashboard")

        if action == "new":
            return redirect("department_master")

        # save / modify
        form = DepartmentForm(
            request.POST,
            instance=department if department else None,
        )
        if form.is_valid():
            form.save()
            return redirect("department_master")
    else:
        form = DepartmentForm(instance=department if department else None)

    departments = Department.objects.order_by("name")

    context = {
        "form": form,
        "departments": departments,
        "selected_department": department,
    }
    return render(request, "masters/department_master.html", context)

def employee_master(request):
    """Master screen for Employee Details."""

    employees = Employee.objects.select_related("department").order_by("employee_id")
    instance = None

    # Edit mode when clicking on list row (?id=123)
    emp_id = request.GET.get("id")
    if emp_id:
        instance = get_object_or_404(Employee, pk=emp_id)

    if request.method == "POST":
        pk = request.POST.get("pk")
        if pk:
            instance = get_object_or_404(Employee, pk=pk)

        # Determine which button was clicked
        if "btn_new" in request.POST:
            return redirect("employee_master")

        if "btn_close" in request.POST:
            return redirect("master_dashboard")  # or wherever you want to go

        form = EmployeeForm(request.POST, instance=instance)
        if "btn_save" in request.POST and form.is_valid():
            emp = form.save()
            return redirect(f"{reverse('employee_master')}?id={emp.pk}")

    else:
        form = EmployeeForm(instance=instance)

    context = {
        "form": form,
        "employees": employees,
        "editing": bool(instance),
    }
    return render(request, "masters/employee_master.html", context)