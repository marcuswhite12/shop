from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
]
