# masters/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages

from .models import Department, Employee, Unit, Product, ProductMaster, TermCondition, Customer, ProductBOM, ProductDevelopment, COMPANY_SIZE_CHOICES
from .forms import DepartmentForm, EmployeeForm, UnitForm, ProductForm
from django.db.models import Q
from datetime import datetime
from django.db import transaction

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
            "url": reverse("unit_master"),
        },
        {
            "title": "Master Product",
            "icon": "img/master_product.png",
            "url": reverse("product_master"),
        },
        {
            "title": "Product Master",
            "icon": "img/master_product_master.png",
            "url": reverse("product_master_detail"),
        },
    ]

    tiles_row2 = [
        {
            "title": "Terms and Conditions",
            "icon": "img/master_terms.png",
            "url": reverse("terms_conditions"),
        },
        {
            "title": "Add New Customer",
            "icon": "img/master_customer.png",
            "url": reverse("customer_master"),
        },
        {
            "title": "Product BOM",
            "icon": "img/master_bom.png",
            "url": reverse("product_bom_master"),
        },
        {
            "title": "Product Development",
            "icon": "img/master_development.png",
            "url": reverse("product_development"),
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

def unit_master(request):
    """
    Simple Unit Master:

    - Left side: form for one unit (create / edit)
    - Right side: table listing all units
    - Clicking a row loads that unit into the form (via ?id=)
    """
    units = Unit.objects.all()

    selected_unit = None

    # If GET has ?id= we load that unit for editing
    unit_id = request.GET.get("id")
    if unit_id:
        selected_unit = get_object_or_404(Unit, pk=unit_id)

    if request.method == "POST":
        # Hidden field in form to know if we're editing
        post_id = request.POST.get("unit_id")
        if post_id:
            selected_unit = get_object_or_404(Unit, pk=post_id)

        form = UnitForm(request.POST, instance=selected_unit)
        if form.is_valid():
            form.save()
            # After save, go back to clean form
            return redirect("unit_master")
    else:
        form = UnitForm(instance=selected_unit)

    context = {
        "form": form,
        "units": units,
    }
    return render(request, "masters/unit_master.html", context)

def product_master(request):
    """
    Simple Product Master – add product name on the left,
    list all products on the right.
    """
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product saved successfully.")
            return redirect("product_master")
    else:
        form = ProductForm()

    products = Product.objects.all()  # ordered by id from Meta

    context = {
        "form": form,
        "products": products,
    }
    return render(request, "masters/product_master.html", context)

def product_master_detail(request):
    """
    Product Master screen:
    - Create detailed product records
    - Show grid with product masters
    """

    products = Product.objects.order_by("name")
    units = Unit.objects.order_by("name")

    q = request.GET.get("q", "").strip()

    rows = (
        ProductMaster.objects.select_related("base_product", "unit")
        .order_by("base_product__name")
    )
    if q:
        rows = rows.filter(
            Q(base_product__name__icontains=q)
            | Q(company_name__icontains=q)
        )

    if request.method == "POST":
        base_product_id = request.POST.get("base_product")
        unit_id = request.POST.get("unit")

        if not base_product_id:
            # minimal validation: just reload
            return redirect("product_master_detail")

        base_product = Product.objects.get(id=base_product_id)
        unit = Unit.objects.get(id=unit_id) if unit_id else None

        def _dec(name):
            val = request.POST.get(name, "").strip()
            return val or None

        ProductMaster.objects.create(
            base_product=base_product,
            unit=unit,
            pack_qty=_dec("pack_qty"),
            incentive=_dec("incentive"),
            solid=_dec("solid"),
            selling_price=_dec("selling_price"),
            packed_in=request.POST.get("packed_in", "").strip(),
            min_stock_level=_dec("min_stock_level"),
            raw_material_cost=_dec("raw_material_cost"),
            density=_dec("density"),
            company_name="DMOR PAINTS",
        )

        return redirect("product_master_detail")

    context = {
        "products": products,
        "units": units,
        "rows": rows,
        "search": q,
    }
    return render(request, "masters/product_master_detail.html", context)

def terms_conditions(request):
    """
    Master screen for Terms & Conditions.
    - GET: show list + empty/edit form
    - POST: create/update/delete
    """
    editing = None

    # DELETE
    if request.method == "POST" and "delete_id" in request.POST:
        delete_id = request.POST.get("delete_id")
        if delete_id:
            TermCondition.objects.filter(pk=delete_id).delete()
        return redirect("terms_conditions")

    # CREATE / UPDATE
    if request.method == "POST":
        term_pk = request.POST.get("term_pk") or None
        term_name = (request.POST.get("term_name") or "").strip()
        conditions = (request.POST.get("conditions") or "").strip()

        if term_pk:  # update existing
            editing = get_object_or_404(TermCondition, pk=term_pk)
            editing.term_name = term_name
            editing.description = conditions
            editing.save()
        else:  # create new
            if term_name:
                TermCondition.objects.create(
                    term_name=term_name,
                    description=conditions,
                )
        return redirect("terms_conditions")

    # LOAD form for edit when clicking row
    edit_id = request.GET.get("edit")
    if edit_id:
        editing = get_object_or_404(TermCondition, pk=edit_id)

    terms = TermCondition.objects.all()
    context = {
        "terms": terms,
        "editing": editing,
    }
    return render(request, "masters/terms_conditions.html", context)

def customer_master(request):
    """
    Add New Customer master screen:
    - GET: show form + list
    - POST: create/update/delete
    """
    editing = None

    # --- DELETE ---
    if request.method == "POST" and "delete_id" in request.POST:
        cid = request.POST.get("delete_id")
        if cid:
            Customer.objects.filter(pk=cid).delete()
        return redirect("customer_master")

    # --- CREATE / UPDATE ---
    if request.method == "POST":
        customer_pk = request.POST.get("customer_pk") or None

        company_name = (request.POST.get("company_name") or "").strip()
        sales_person_id = request.POST.get("sales_person") or ""
        address = (request.POST.get("address") or "").strip()
        city = (request.POST.get("city") or "").strip()
        landline_no = (request.POST.get("landline_no") or "").strip()
        manager_name = (request.POST.get("manager_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        proprietor_dob_raw = request.POST.get("proprietor_dob") or ""
        company_size = request.POST.get("company_size") or ""
        location = (request.POST.get("location") or "").strip()
        gst_no = (request.POST.get("gst_no") or "").strip()
        proprietor_name = (request.POST.get("proprietor_name") or "").strip()
        mobile_no1 = (request.POST.get("mobile_no1") or "").strip()
        mobile_no2 = (request.POST.get("mobile_no2") or "").strip()
        reference_name = (request.POST.get("reference_name") or "").strip()

        # parse date from HTML date input (YYYY-MM-DD)
        proprietor_dob = None
        if proprietor_dob_raw:
            try:
                proprietor_dob = datetime.strptime(proprietor_dob_raw, "%Y-%m-%d").date()
            except ValueError:
                proprietor_dob = None

        sales_person = None
        if sales_person_id:
            try:
                sales_person = Employee.objects.get(pk=sales_person_id)
            except Employee.DoesNotExist:
                sales_person = None

        data = {
            "company_name": company_name,
            "sales_person": sales_person,
            "address": address,
            "city": city,
            "landline_no": landline_no,
            "manager_name": manager_name,
            "email": email,
            "proprietor_dob": proprietor_dob,
            "company_size": company_size,
            "location": location,
            "gst_no": gst_no,
            "proprietor_name": proprietor_name,
            "mobile_no1": mobile_no1,
            "mobile_no2": mobile_no2,
            "reference_name": reference_name,
        }

        if customer_pk:  # update
            obj = get_object_or_404(Customer, pk=customer_pk)
            for field, value in data.items():
                setattr(obj, field, value)
            obj.save()
        else:           # create
            if company_name:  # simple required field
                Customer.objects.create(**data)

        return redirect("customer_master")

    # --- GET (optionally editing) ---
    edit_id = request.GET.get("edit")
    if edit_id:
        editing = get_object_or_404(Customer, pk=edit_id)

    customers = Customer.objects.select_related("sales_person").all()
    sales_people = Employee.objects.order_by("full_name", "first_name")

    context = {
        "customers": customers,
        "sales_people": sales_people,
        "editing": editing,
        "COMPANY_SIZE_CHOICES": COMPANY_SIZE_CHOICES,
    }
    return render(request, "masters/customer_master.html", context)

@transaction.atomic
def product_bom_master(request):
    products = Product.objects.order_by("name")
    bom_list = ProductBOM.objects.select_related("category").order_by("category__name")

    # defaults for re-populating form
    form_category_id = ""
    form_per_percent = ""
    form_density = ""
    form_hours = ""

    if request.method == "POST":
        form_category_id = request.POST.get("category_id", "").strip()
        form_per_percent = request.POST.get("per_percent", "").strip()
        form_density = request.POST.get("density", "").strip()
        form_hours = request.POST.get("hours", "").strip()

        if not form_category_id or not form_per_percent:
            messages.error(request, "Category and Per % are required.")
        else:
            try:
                category = Product.objects.get(id=form_category_id)

                # convert numeric fields safely
                per_val = float(form_per_percent) if form_per_percent else 0
                dens_val = float(form_density) if form_density else None
                hours_val = float(form_hours) if form_hours else None

                obj, created = ProductBOM.objects.update_or_create(
                    category=category,
                    defaults={
                        "per_percent": per_val,
                        "density": dens_val,
                        "hours": hours_val,
                        "is_active": True,
                    },
                )
                messages.success(
                    request,
                    f"Product BOM for '{category.name}' has been "
                    f"{'created' if created else 'updated'}.",
                )
                # clear form after save
                return redirect("product_bom_master")
            except Product.DoesNotExist:
                messages.error(request, "Selected category not found.")

    context = {
        "products": products,
        "bom_list": bom_list,
        "form_category_id": form_category_id,
        "form_per_percent": form_per_percent,
        "form_density": form_density,
        "form_hours": form_hours,
    }
    return render(request, "masters/product_bom_master.html", context)

@transaction.atomic
def product_development(request):
    products = Product.objects.order_by("name")
    dev_list = ProductDevelopment.objects.select_related("category").order_by("category__name")

    # Keep form values if validation fails
    form_category_id = ""
    form_per_percent = ""
    form_density = ""
    form_hours = ""

    if request.method == "POST":
        form_category_id = request.POST.get("category_id", "").strip()
        form_per_percent = request.POST.get("per_percent", "").strip()
        form_density = request.POST.get("density", "").strip()
        form_hours = request.POST.get("hours", "").strip()

        if not form_category_id or not form_per_percent:
            messages.error(request, "Category and Per % are required.")
        else:
            try:
                category = Product.objects.get(id=form_category_id)

                per_val = float(form_per_percent) if form_per_percent else 0
                dens_val = float(form_density) if form_density else None
                hours_val = float(form_hours) if form_hours else None

                obj, created = ProductDevelopment.objects.update_or_create(
                    category=category,
                    defaults={
                        "per_percent": per_val,
                        "density": dens_val,
                        "hours": hours_val,
                        "is_active": True,
                    },
                )
                messages.success(
                    request,
                    f"Product development for '{category.name}' has been "
                    f"{'created' if created else 'updated'}.",
                )
                return redirect("product_development")
            except Product.DoesNotExist:
                messages.error(request, "Selected category not found.")

    context = {
        "products": products,
        "dev_list": dev_list,
        "form_category_id": form_category_id,
        "form_per_percent": form_per_percent,
        "form_density": form_density,
        "form_hours": form_hours,
    }
    return render(request, "masters/product_development.html", context)