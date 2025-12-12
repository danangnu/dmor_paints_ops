# masters/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal, InvalidOperation

from .models import (
    Department,
    Employee,
    Unit,
    Product,
    ProductMaster,
    TermCondition,
    Customer,
    ProductBOM,
    ProductDevelopment,
    ProductBOMItem,
    ProductDevelopmentItem,
    COMPANY_SIZE_CHOICES,
)
from .forms import DepartmentForm, EmployeeForm, UnitForm, ProductForm
from django.db.models import Q
from datetime import datetime
from django.db import transaction
from django.utils import timezone

# ----------------------------------------------------------------------
# Packed In options (used in Product Master "Packed In" dropdown)
# ----------------------------------------------------------------------
PACKED_IN_CHOICES = [
    "BUCKETS 20LTRS WITHOUT NAME",
    "BUCKET 10KG",
    "BUCKET 5KG",
    "BAG 20 KG",
    "BUCKET 20LTR HYDE",
    "BUCKET 1KG CRACKFILL",
    "BUCKET 1KG HERO",
    "BUCKET 10 LTRS WITHOUT NAME",
    "BUCKET 20KG",
    "10 LTR TIN",
    "BUCKET 4LTR WITHOUT NAME",
    "BUCKET 1LTR WITHOUT NAME",
    "BAG 40KG",
    "4 Ltr Tin",
    "5 Ltr Can",
    "500ml Tin",
    # add more as needed
]


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
        )

    # default inventory type for first load
    current_inventory_type = ProductMaster.INVENTORY_TYPE_FINISHED

    if request.method == "POST":
        base_product_id = request.POST.get("base_product")
        unit_id = request.POST.get("unit")
        inventory_type = request.POST.get("inventory_type") or ProductMaster.INVENTORY_TYPE_FINISHED
        current_inventory_type = inventory_type

        if not base_product_id:
            # minimal validation: just reload
            return redirect("product_master_detail")

        base_product = Product.objects.get(id=base_product_id)
        unit = Unit.objects.get(id=unit_id) if unit_id else None

        def _dec(name: str):
            raw = (request.POST.get(name) or "").strip()
            if not raw:
                return None

            # force dot-decimal: convert comma to dot just in case
            raw = raw.replace(",", ".")

            try:
                return Decimal(raw)
            except InvalidOperation:
                # invalid number -> treat as empty
                return None

        # initial values from form
        solid_val = _dec("solid")
        density_val = _dec("density")
        packed_in_val = (request.POST.get("packed_in") or "").strip()

        # Business rules based on inventory type:
        # - RAW MATERIAL: has density & solids, no packed_in
        # - FINISHED GOODS / PACKING MATERIAL: use packed_in, ignore density & solids
        if inventory_type == ProductMaster.INVENTORY_TYPE_RAW:
            packed_in_val = ""
        else:
            solid_val = None
            density_val = None

        ProductMaster.objects.create(
            base_product=base_product,
            unit=unit,
            inventory_type=inventory_type,
            pack_qty=_dec("pack_qty"),
            incentive=_dec("incentive"),
            solid=solid_val,
            selling_price=_dec("selling_price"),
            packed_in=packed_in_val,
            min_stock_level=_dec("min_stock_level"),
            raw_material_cost=_dec("raw_material_cost"),
            density=density_val,
            company_name="DMOR PAINTS",
        )

        return redirect("product_master_detail")

    context = {
        "products": products,
        "units": units,
        "rows": rows,
        "search": q,
        "packed_in_choices": PACKED_IN_CHOICES,
        "INVENTORY_TYPE_CHOICES": ProductMaster.INVENTORY_TYPE_CHOICES,
        "current_inventory_type": current_inventory_type,
    }
    return render(request, "masters/product_master_detail.html", context)


def product_master_detail_delete(request, pk):
    if request.method == "POST":
        obj = get_object_or_404(ProductMaster, pk=pk)
        obj.delete()
        messages.success(request, "Product master record deleted.")
    # whether it was POST or not, go back to the listing
    return redirect("product_master_detail")


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

        # ---------- UNIQUENESS CHECKS ----------
        # gst_no, mobile_no1 and mobile_no2 must be unique across all customers
        has_conflict = False

        # GST No uniqueness (case-insensitive)
        if gst_no:
            qs = Customer.objects.filter(gst_no__iexact=gst_no)
            if customer_pk:
                qs = qs.exclude(pk=customer_pk)
            if qs.exists():
                messages.error(request, "GST No is already used by another customer.")
                has_conflict = True

        # Mobile 1 uniqueness (cannot match any customer's mobile1 or mobile2)
        if mobile_no1:
            qs = Customer.objects.filter(
                Q(mobile_no1=mobile_no1) | Q(mobile_no2=mobile_no1)
            )
            if customer_pk:
                qs = qs.exclude(pk=customer_pk)
            if qs.exists():
                messages.error(request, "Mobile No 1 is already used by another customer.")
                has_conflict = True

        # Mobile 2 uniqueness (cannot match any customer's mobile1 or mobile2)
        if mobile_no2:
            qs = Customer.objects.filter(
                Q(mobile_no1=mobile_no2) | Q(mobile_no2=mobile_no2)
            )
            if customer_pk:
                qs = qs.exclude(pk=customer_pk)
            if qs.exists():
                messages.error(request, "Mobile No 2 is already used by another customer.")
                has_conflict = True

        # if any conflict, abort save and reload screen
        if has_conflict:
            return redirect("customer_master")
        # ---------- END UNIQUENESS CHECKS ----------

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

    def _to_float(raw: str):
        raw = (raw or "").strip().replace(",", ".")
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def _to_decimal(raw: str, default=Decimal("0.00")):
        raw = (raw or "").strip().replace(",", ".")
        if not raw:
            return default
        try:
            return Decimal(raw)
        except InvalidOperation:
            return default

    def _to_int(raw: str, default=0):
        raw = (raw or "").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

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

                # convert numeric fields safely (header)
                per_val = _to_float(form_per_percent) or 0
                dens_val = _to_float(form_density)
                hours_val = _to_float(form_hours)

                bom_obj, created = ProductBOM.objects.update_or_create(
                    category=category,
                    defaults={
                        "per_percent": per_val,
                        "density": dens_val,
                        "hours": hours_val,
                        "is_active": True,
                    },
                )

                # ----- SAVE GRID LINE ITEMS -----
                # Saves percent_<productId> and seq_<productId> into ProductBOMItem
                # If the grid is shown, this will update/create items for all products.
                for p in products:
                    percent_val = _to_decimal(request.POST.get(f"percent_{p.id}"), default=Decimal("0.00"))
                    seq_val = _to_int(request.POST.get(f"seq_{p.id}"), default=0)

                    ProductBOMItem.objects.update_or_create(
                        bom=bom_obj,
                        product=p,
                        defaults={
                            "percent": percent_val,
                            "sequence": seq_val,
                        },
                    )
                # ----- END SAVE GRID LINE ITEMS -----

                messages.success(
                    request,
                    f"Product BOM for '{category.name}' has been "
                    f"{'created' if created else 'updated'}.",
                )

                # keep same category selected after save
                return redirect(f"{reverse('product_bom_master')}?category_id={category.id}")

            except Product.DoesNotExist:
                messages.error(request, "Selected category not found.")

    else:
        # GET: when user clicks category, we pass ?category_id=...
        form_category_id = request.GET.get("category_id", "").strip()

    # show detail grid only if a category is selected
    show_bom_table = bool(form_category_id)

    context = {
        "products": products,
        "bom_list": bom_list,
        "form_category_id": form_category_id,
        "form_per_percent": form_per_percent,
        "form_density": form_density,
        "form_hours": form_hours,
        "show_bom_table": show_bom_table,
    }
    return render(request, "masters/product_bom_master.html", context)

def _dec_dot(val: str, default: str = "0") -> Decimal:
    """
    Safe Decimal parser:
    - empty => default
    - comma not allowed (enforces dot decimals)
    """
    s = (val or "").strip()
    if s == "":
        return Decimal(default)
    if "," in s:
        raise InvalidOperation("Comma decimal not allowed")
    return Decimal(s)


@transaction.atomic
def product_development(request):
    products = Product.objects.order_by("name")

    form_category_id = ""
    form_per_percent = ""
    form_density = ""
    form_hours = ""

    development = None
    items_by_pid = {}  # product_id -> ProductDevelopmentItem

    # bottom totals
    total_volume = Decimal("0.000")
    total_sv = Decimal("0.000")
    solid_volume_ratio = Decimal("0.00")

    # right table
    summary_rows = []

    # -------------------------
    # POST (SAVE)
    # -------------------------
    if request.method == "POST":
        form_category_id = request.POST.get("category_id", "").strip()
        form_per_percent = request.POST.get("per_percent", "").strip()
        form_density = request.POST.get("density", "").strip()
        form_hours = request.POST.get("hours", "").strip()

        if not form_category_id or not form_per_percent:
            messages.error(request, "Category and Per % are required.")
        else:
            try:
                category = Product.objects.get(pk=form_category_id)

                per_percent = _dec_dot(form_per_percent, "0")
                density_hdr = _dec_dot(form_density, "0")
                hours = _dec_dot(form_hours, "0")

                development, _ = ProductDevelopment.objects.update_or_create(
                    category=category,
                    defaults={
                        "per_percent": per_percent,
                        "density": density_hdr,
                        "hours": hours,
                        "is_active": True,
                        "created_at": timezone.now(),
                    },
                )

                # Save rows
                for p in products:
                    percent = _dec_dot(request.POST.get(f"percent_{p.id}"), "0")
                    seq = int((request.POST.get(f"seq_{p.id}") or "0").strip() or "0")
                    rate = _dec_dot(request.POST.get(f"rate_{p.id}"), "0")
                    solid_percent = _dec_dot(request.POST.get(f"solidp_{p.id}"), "0")
                    dens = _dec_dot(request.POST.get(f"dens_{p.id}"), "0")

                    # ---- LEGACY CALCS (server-side) ----
                    amount = percent * rate
                    solid = percent * (solid_percent / Decimal("100"))
                    wt_ltr = (percent / dens) if dens > 0 else Decimal("0")
                    sv = (solid / dens) if dens > 0 else Decimal("0")

                    # Skip truly empty
                    if percent == 0 and rate == 0 and solid_percent == 0 and dens == 0:
                        # If row existed earlier, you may want to delete it:
                        ProductDevelopmentItem.objects.filter(
                            development=development, product=p
                        ).delete()
                        continue

                    ProductDevelopmentItem.objects.update_or_create(
                        development=development,
                        product=p,
                        defaults={
                            "percent": percent,
                            "sequence": seq,
                            "rate": rate,
                            "amount": amount,
                            "solid_percent": solid_percent,
                            "solid": solid,
                            "density": dens,
                            "wt_ltr": wt_ltr,
                            "sv": sv,
                        },
                    )

                messages.success(request, "Product Development saved successfully.")
                return redirect(f"{reverse('product_development')}?category_id={category.id}")

            except Product.DoesNotExist:
                messages.error(request, "Selected category not found.")
            except (InvalidOperation, ValueError):
                messages.error(request, "Invalid number format. Use dot (.) for decimals only.")

    # -------------------------
    # GET (LOAD)
    # -------------------------
    else:
        form_category_id = request.GET.get("category_id", "").strip()

    if form_category_id:
        development = ProductDevelopment.objects.filter(category_id=form_category_id).first()
        if development:
            form_per_percent = development.per_percent
            form_density = development.density
            form_hours = development.hours

            dev_items = (
                ProductDevelopmentItem.objects
                .filter(development=development)
                .select_related("product")
                .order_by("sequence", "id")
            )

            # map for template defaults
            items_by_pid = {it.product_id: it for it in dev_items}

            # totals
            perkg_cost = Decimal("0.000")
            for it in dev_items:
                total_volume += (it.wt_ltr or Decimal("0"))
                total_sv += (it.sv or Decimal("0"))
                perkg_cost += (it.amount or Decimal("0"))

            if total_volume > 0:
                solid_volume_ratio = (total_sv / total_volume) * Decimal("100")

            # -------------------------
            # LEGACY RIGHT BOX
            # -------------------------
            # Finished goods master for this category
            fg_master = (
                ProductMaster.objects
                .select_related("base_product", "unit")
                .filter(
                    base_product_id=form_category_id,
                    inventory_type=ProductMaster.INVENTORY_TYPE_FINISHED,
                )
                .first()
            )

            if fg_master:
                pack_qty = fg_master.pack_qty or Decimal("1")
                selling_price = fg_master.selling_price or Decimal("0")

                # packing cost from packing material by name == packed_in
                packing_cost = Decimal("0.00")
                if fg_master.packed_in:
                    pm = (
                        ProductMaster.objects
                        .select_related("base_product")
                        .filter(
                            inventory_type=ProductMaster.INVENTORY_TYPE_PACKING,
                            base_product__name__iexact=fg_master.packed_in.strip(),
                        )
                        .first()
                    )
                    if pm and pm.selling_price:
                        packing_cost = pm.selling_price

                per_ltr_cost_price = (perkg_cost / total_volume) if total_volume > 0 else Decimal("0")
                production_cost = (per_ltr_cost_price * pack_qty) + packing_cost
                gross_profit = selling_price - production_cost

                summary_rows.append({
                    "product_name": fg_master.base_product.name,
                    "pack_qty": pack_qty,
                    "unit_selling_rate": (selling_price / pack_qty) if pack_qty > 0 else Decimal("0"),
                    "perkg_cost": perkg_cost,
                    "packing_cost": packing_cost,
                    "per_ltr_cost_price": per_ltr_cost_price,
                    "production_cost": production_cost,
                    "gross_profit": gross_profit,
                })

    context = {
        "products": products,
        "development": development,
        "items_by_pid": items_by_pid,
        "form_category_id": form_category_id,
        "form_per_percent": form_per_percent,
        "form_density": form_density,
        "form_hours": form_hours,
        "show_dev_table": bool(form_category_id),

        # bottom totals
        "solid_volume_ratio": solid_volume_ratio.quantize(Decimal("0.01")),
        "total_volume": total_volume.quantize(Decimal("0.01")),

        # right box
        "summary_rows": summary_rows,
    }
    return render(request, "masters/product_development.html", context)