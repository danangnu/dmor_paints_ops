# masters/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.master_dashboard, name="master_dashboard"),

    # Department Master
    path("departments/", views.department_master, name="department_master"),
    path("departments/<int:pk>/", views.department_master, name="department_edit"),
    path("employee-master/", views.employee_master, name="employee_master"),
    path("units/", views.unit_master, name="unit_master"),
    path("product-master/", views.product_master, name="product_master"),
    path("product-master-detail/", views.product_master_detail, name="product_master_detail"),
    path(
        "product-master-detail/<int:pk>/delete/",
        views.product_master_detail_delete,
        name="product_master_detail_delete",
    ),
    path("terms-conditions/", views.terms_conditions, name="terms_conditions"),
    path("customers/", views.customer_master, name="customer_master"),
    path("product-bom/", views.product_bom_master, name="product_bom_master"),
    path("product-development/", views.product_development, name="product_development"),
]