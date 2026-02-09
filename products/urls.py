from django.urls import path
from .views import CategoryListView, ProductListView, ProductDetailView

urlpatterns = [
    path('', CategoryListView.as_view(), name='home'),
    path('category/<slug:slug>/', ProductListView.as_view(), name='category_detail'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]