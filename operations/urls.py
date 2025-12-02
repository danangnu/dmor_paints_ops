from django.urls import path
from . import views

urlpatterns = [
    path("", views.operation_dashboard, name="operation_dashboard"),
    path("create-order/", views.create_order, name="create_order"),
    path("payments/", views.payment_clearance, name="payment_clearance"),
    path("factory-status/", views.factory_status, name="factory_status"),
    path("bom-production/", views.bom_production, name="bom_production"),
]