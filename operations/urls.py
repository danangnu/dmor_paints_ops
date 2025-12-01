from django.urls import path
from . import views

urlpatterns = [
    path('', views.operation_dashboard, name='operation_dashboard'),
]