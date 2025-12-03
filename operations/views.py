from django.shortcuts import render, redirect, get_object_or_404
from .forms import OrderForm, BatchForm, BatchItemForm, DispatchHeaderForm, MaterialInwardForm, MaterialDiscardForm
from .models import Order, FactoryOrder, Batch, BatchItem, Dispatch, DispatchItem, Vehicle, MaterialReturn, MasterProduct
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.urls import reverse 

def operation_dashboard(request):
    tiles = [
        {"title": "CREATE ORDER",               "icon": "img/create_order.png",              "url": reverse("create_order")},
        {"title": "ADMIN-ACCOUNTS CLEARANCE",   "icon": "img/admin_accounts_clearance.png",  "url": reverse("payment_clearance")},
        {"title": "PM-ORDER ACCEPTANCE",        "icon": "img/pm_order_acceptance.png",       "url": reverse("factory_status")},
        {"title": "PM-PREPARE BATCH CHART",     "icon": "img/pm_prepare_batch_chart.png",    "url": reverse("bom_production")},
        {"title": "DISPATCH PLANNING",          "icon": "img/dispatch_planning.png",         "url": reverse("dispatch_order")},
        {"title": "PM-MATERIAL INWORD",         "icon": "img/pm_material_inword.png",        "url": reverse("material_inward")},
        {"title": "PM-SPLIT ORDER",             "icon": "img/pm_split_order.png",            "url": reverse("split_order")},
        {"title": "ADMIN-MATERIAL DISCARD",     "icon": "img/admin_material_discard.png",    "url": reverse("material_discard")},
        {"title": "PM-RETURN INWORD",           "icon": "img/pm_return_inword.png",          "url": reverse("material_inward_back")},
        {"title": "UPDATE PRODUCT",             "icon": "img/update_product.png",            "url": reverse("update_products")},
    ]

    context = {
        "row1": tiles[:6],   # first 7
        "row2": tiles[6:],   # last 3 (here 3+1 = 4)
    }
    return render(request, "operations/dashboard.html", context)

def create_order(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            # after saving, go back to dashboard (or to a "success" page)
            return redirect("operation_dashboard")
    else:
        form = OrderForm()

    return render(request, "operations/create_order.html", {"form": form})

def payment_clearance(request):
    """
    Payment clearance screen:
    - Top table  : active orders (not on hold)
    - Bottom table: orders on hold
    """
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        action = request.POST.get("action")  # e.g. "clear", "hold", "unhold"
        order = get_object_or_404(Order, pk=order_id)

        if action == "clear":
            order.payment_cleared = True
            order.on_hold = False
        elif action == "hold":
            order.on_hold = True
        elif action == "unhold":
            order.on_hold = False

        order.save()
        return redirect("payment_clearance")  # or your url name

    # ---------- HERE IS THE IMPORTANT PART ----------
    orders_active = (
        Order.objects
        .filter(on_hold=False, is_cancelled=False)
        .order_by("-order_created")
    )
    orders_on_hold = (
        Order.objects
        .filter(on_hold=True, is_cancelled=False)
        .order_by("-order_created")
    )
    # ------------------------------------------------

    context = {
        "orders_active": orders_active,
        "orders_on_hold": orders_on_hold,
    }
    return render(request, "operations/payment_clearance.html", context)

def factory_status(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        action = request.POST.get("action")

        order = get_object_or_404(FactoryOrder, pk=order_id)

        # update editable fields
        order.delivery_expected_date = request.POST.get("delivery_expected_date") or None
        order.remark = request.POST.get("remark") or ""

        if action == "toggle_accept":
            order.factory_accepted = not order.factory_accepted

        order.save()
        return redirect("factory_status")

    orders = FactoryOrder.objects.all().order_by("-order_id")
    return render(request, "operations/factory_status.html", {"orders": orders})

def bom_production(request):
    batch_form = BatchForm()
    item_form = BatchItemForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "start_batch":
            batch_form = BatchForm(request.POST)
            item_form = BatchItemForm(request.POST)

            if batch_form.is_valid():
                batch = batch_form.save()

                # if product + qty filled, create first line
                if item_form.is_valid() and item_form.cleaned_data.get("product"):
                    BatchItem.objects.create(
                        batch=batch,
                        product=item_form.cleaned_data["product"],
                        qty=item_form.cleaned_data["qty"],
                    )

                return redirect("bom_production")

        elif action == "end_batch":
            batch_id = request.POST.get("batch_id")
            if batch_id:
                try:
                    batch = Batch.objects.get(pk=batch_id)
                    batch.status = "FINISHED"
                    batch.ended_at = timezone.now()
                    batch.save()
                except Batch.DoesNotExist:
                    pass
            return redirect("bom_production")

    # show latest 10 batches
    batches = Batch.objects.order_by("-started_at")[:10]

    context = {
        "batch_form": batch_form,
        "item_form": item_form,
        "batches": batches,
    }
    return render(request, "operations/bom_production.html", context)

def dispatch_order(request):
    header_form = DispatchHeaderForm()
    load_info = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_dispatch":
            header_form = DispatchHeaderForm(request.POST)
            if header_form.is_valid():
                dispatch = header_form.save(commit=False)
                dispatch.created_at = timezone.now()
                dispatch.save()

                selected_ids = request.POST.getlist("selected_items")
                items = DispatchItem.objects.filter(
                    id__in=selected_ids, dispatch__isnull=True
                )

                for item in items:
                    item.dispatch = dispatch
                    item.dispatch_date = timezone.now().date()
                    item.save()

                return redirect("dispatch_order")

        elif action == "estimate_load":
            # just calculate load for selected vehicle
            header_form = DispatchHeaderForm(request.POST)
            if header_form.is_valid():
                vehicle = header_form.cleaned_data["vehicle"]
                selected_ids = request.POST.getlist("selected_items")
                items = DispatchItem.objects.filter(
                    id__in=selected_ids, dispatch__isnull=True
                )
                total_qty = sum((i.qty for i in items), 0)
                pct = float(total_qty) / float(vehicle.capacity_qty) * 100 if vehicle.capacity_qty else 0
                load_info = {
                    "vehicle": vehicle,
                    "total_qty": total_qty,
                    "capacity": vehicle.capacity_qty,
                    "percent": pct,
                }

    # pending rows (not dispatched yet)
    pending_items = DispatchItem.objects.filter(dispatch__isnull=True).order_by("order_id")

    context = {
        "header_form": header_form,
        "pending_items": pending_items,
        "load_info": load_info,
    }
    return render(request, "operations/dispatch_order.html", context)

def material_inward(request):
    if request.method == "POST":
        form = MaterialInwardForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Material inward saved.")
            return redirect("material_inward")
    else:
        form = MaterialInwardForm()

    return render(request, "operations/material_inward.html", {"form": form})

def split_cancel_order(request):
    # show only non-cancelled orders
    orders = Order.objects.filter(is_cancelled=False).order_by("id")

    if request.method == "POST":
        action = request.POST.get("action")
        order_id = request.POST.get("order_id")

        if not order_id:
            messages.error(request, "Please select an order first.")
            return redirect("split_cancel_order")

        order = get_object_or_404(Order, id=order_id)

        if action == "split":
            try:
                split_qty_raw = request.POST.get("split_qty") or "0"
                split_qty = float(split_qty_raw)
            except ValueError:
                messages.error(request, "Split quantity must be a number.")
                return redirect("split_cancel_order")

            if split_qty <= 0 or split_qty >= float(order.quantity):
                messages.error(request, "Invalid split quantity.")
                return redirect("split_cancel_order")

            # reduce quantity on original order
            order.quantity = float(order.quantity) - split_qty
            order.is_split = True
            order.save()

            # create new order row for the split part
            Order.objects.create(
                company=order.company,
                address=order.address,
                city=order.city,
                sales_person=order.sales_person,
                location=order.location,
                mobile1=order.mobile1,
                mobile2=order.mobile2,
                product_name=order.product_name,
                quantity=split_qty,
                price=order.price,
                discount=order.discount,
                discount_amount=order.discount_amount,
                total_price=order.price * split_qty,  # simple calc, adjust if needed
                remark=order.remark,
                order_created=order.order_created,
                bill_no=order.bill_no,
                payment_cleared=order.payment_cleared,
                factory_accepted=order.factory_accepted,
                available_qty=order.available_qty,
                dispatch_date=order.dispatch_date,
                time_span_text=order.time_span_text,
            )

            messages.success(request, "Order successfully split.")

        elif action == "cancel":
            order.is_cancelled = True
            order.save()
            messages.success(request, "Order cancelled successfully.")

        return redirect("split_cancel_order")

    return render(request, "operations/split_cancel_order.html", {"orders": orders})


def split_or_cancel_order(request):
    """
    Screen where accounts can split or cancel orders.
    Shows all non-cancelled orders (you can tighten filter later).
    """
    message = ""
    error = ""

    # you can adjust this filter as needed:
    orders = (
        Order.objects.filter(is_cancelled=False)
        .order_by("-order_created")
    )

    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_orders")
        remark = (request.POST.get("remark") or "").strip()
        action = request.POST.get("action")  # "split" or "cancel"

        if not selected_ids:
            error = "Please select at least one order."
        elif action not in ("split", "cancel"):
            error = "Unknown action."
        else:
            qs = Order.objects.filter(id__in=selected_ids)

            with transaction.atomic():
                for order in qs:
                    # append remark if user typed something
                    if remark:
                        if order.remark:
                            order.remark = f"{order.remark}\n{remark}"
                        else:
                            order.remark = remark

                    if action == "split":
                        order.is_split = True
                    elif action == "cancel":
                        order.is_cancelled = True

                    order.save()

            if action == "split":
                message = f"{qs.count()} order(s) marked as split."
            else:
                message = f"{qs.count()} order(s) cancelled."

            # reload list after update
            return redirect("split-order")

    context = {
        "orders": orders,
        "message": message,
        "error": error,
    }
    return render(request, "operations/split_order.html", context)

def material_discard(request):
    """
    Simple screen to log discarding either Raw Material (RM)
    or Finished Goods (FG).
    """
    if request.method == "POST":
        form = MaterialDiscardForm(request.POST)
        if form.is_valid():
            form.save()
            # after save go back to dashboard (or wherever you like)
            return redirect("dashboard")
    else:
        form = MaterialDiscardForm()

    context = {
        "form": form,
        "page_title": "Material Discard",
        "section_title": "Material Discard",
    }
    return render(request, "operations/material_discard.html", context)

def material_inward_back(request):
    returned_items = MaterialReturn.objects.order_by("-returned_at")

    context = {
        "returned_items": returned_items,
        "page_title": "Inward Returned Material",
    }
    return render(request, "operations/material_inward_back.html", context)

def update_products(request):
    # Which tab? default FG
    current_type = request.GET.get("type", "FG")
    if current_type not in ("FG", "RM", "PK"):
        current_type = "FG"

    # Search query
    q = request.GET.get("q", "").strip()

    products = MasterProduct.objects.filter(product_type=current_type)
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(code__icontains=q)
        )

    if request.method == "POST":
        # We keep the same filter when saving
        products = MasterProduct.objects.filter(product_type=current_type)
        for p in products:
            sp_field = f"selling_price_{p.id}"
            pp_field = f"purchase_price_{p.id}"
            sp_val = request.POST.get(sp_field)
            pp_val = request.POST.get(pp_field)
            if sp_val is not None and sp_val != "":
                try:
                    p.selling_price = sp_val
                except ValueError:
                    pass
            if pp_val is not None and pp_val != "":
                try:
                    p.purchase_price = pp_val
                except ValueError:
                    pass
            p.save()
        # back to GET so refresh uses query params
        return redirect(
            f"{request.path}?type={current_type}&q={q}"
        )

    context = {
        "products": products,
        "current_type": current_type,
        "q": q,
    }
    return render(request, "operations/update_products.html", context)

def masters_dashboard(request):
    """
    Masters home – tiles for Department, Designation, Employee Master, etc.
    """
    row1 = [
        {"title": "Department",        "icon": "img/master_department.png", "url": "#"},
        {"title": "Designation",       "icon": "img/master_designation.png", "url": "#"},
        {"title": "Employee Master",   "icon": "img/master_employee.png",    "url": "#"},
        {"title": "Unit Master",       "icon": "img/master_unit.png",        "url": "#"},
        {"title": "Master Product",    "icon": "img/master_product.png",     "url": "#"},
        {"title": "Product Master",    "icon": "img/master_product_master.png", "url": "#"},
    ]

    row2 = [
        {"title": "Terms and Conditions", "icon": "img/master_terms.png",      "url": "#"},
        {"title": "ADD NEW CUSTOMER",     "icon": "img/master_customer.png",  "url": "#"},
        {"title": "Product BOM",          "icon": "img/master_bom.png",       "url": "#"},
        {"title": "PRODUCT DEVELOPMENT",  "icon": "img/master_development.png","url": "#"},
    ]

    context = {
        "row1": row1,
        "row2": row2,
    }
    return render(request, "operations/masters_dashboard.html", context)