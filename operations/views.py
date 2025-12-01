from django.shortcuts import render

def operation_dashboard(request):
    tiles = [
        {"title": "CREATE ORDER",               "icon": "img/create_order.png",              "url": "#"},
        {"title": "ADMIN-ACCOUNTS CLEARANCE",   "icon": "img/admin_accounts_clearance.png",  "url": "#"},
        {"title": "PM-ORDER ACCEPTANCE",        "icon": "img/pm_order_acceptance.png",       "url": "#"},
        {"title": "PM-PREPARE BATCH CHART",     "icon": "img/pm_prepare_batch_chart.png",    "url": "#"},
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