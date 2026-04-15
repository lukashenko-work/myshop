from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='catalog'),
    path('product-<slug:slug>/', views.ProductDetailView.as_view(), name='product')
]
