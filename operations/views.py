from django.shortcuts import render, redirect, get_object_or_404
from .forms import OrderForm, BatchForm, BatchItemForm
from .models import Order, FactoryOrder, Batch, BatchItem
from django.utils import timezone

def operation_dashboard(request):
    tiles = [
        {"title": "CREATE ORDER",               "icon": "img/create_order.png",              "url": "/create-order/"},
        {"title": "ADMIN-ACCOUNTS CLEARANCE",   "icon": "img/admin_accounts_clearance.png",  "url": "/payments/"},
        {"title": "PM-ORDER ACCEPTANCE",        "icon": "img/pm_order_acceptance.png",       "url": "/factory-status/"},
        {"title": "PM-PREPARE BATCH CHART",     "icon": "img/pm_prepare_batch_chart.png",    "url": "/bom-production/"},
        {"title": "DISPATCH PLANNING",          "icon": "img/dispatch_planning.png",         "url": "#"},
        {"title": "PM-MATERIAL INWORD",         "icon": "img/pm_material_inword.png",        "url": "#"},
        {"title": "PM-SPLIT ORDER",             "icon": "img/pm_split_order.png",            "url": "#"},
        {"title": "ADMIN-MATERIAL DISCARD",     "icon": "img/admin_material_discard.png",    "url": "#"},
        {"title": "PM-RETURN INWORD",           "icon": "img/pm_return_inword.png",          "url": "#"},
        {"title": "UPDATE PRODUCT",             "icon": "img/update_product.png",            "url": "#"},
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
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        action = request.POST.get("action")  # 'save', 'hold', 'cancel_hold'
        order = get_object_or_404(Order, pk=order_id)

        # common fields updated from the row
        order.bill_no = request.POST.get("bill_no") or ""
        order.payment_cleared = bool(request.POST.get("payment_cleared"))
        order.payment_remark = request.POST.get("payment_remark") or ""

        # action-specific flags
        if action == "hold":
            order.on_hold = True
        elif action == "cancel_hold":
            order.on_hold = False
        # if action == 'save' → on_hold stays as is

        order.save()
        return redirect("payment_clearance")

    # GET: show page
    orders_active = Order.objects.filter(on_hold=False).order_by("-created_at")
    orders_on_hold = Order.objects.filter(on_hold=True).order_by("-created_at")

    return render(
        request,
        "operations/payment_clearance.html",
        {
            "orders_active": orders_active,
            "orders_on_hold": orders_on_hold,
        },
    )

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