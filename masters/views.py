# masters/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Department
from .forms import DepartmentForm

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
            "url": "#",
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