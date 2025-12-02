from django.urls import path
from . import views

urlpatterns = [
    path("", views.operation_dashboard, name="operation_dashboard"),
    path("create-order/", views.create_order, name="create_order"),
    path("payments/", views.payment_clearance, name="payment_clearance"),
    path("factory-status/", views.factory_status, name="factory_status"),
    path("bom-production/", views.bom_production, name="bom_production"),
    path("dispatch-order/", views.dispatch_order, name="dispatch_order"),
    path("material-inward/", views.material_inward, name="material_inward"),
    path("split-order/", views.split_or_cancel_order, name="split-order"),
]