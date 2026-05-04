from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.CartAddView.as_view(), name='cart_add'),
    path('cart/remove/<int:product_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('success/<int:order_id>/', views.OrderSuccessView.as_view(), name='success'),
    path('cart/addAJAX/<int:product_id>/', views.CartAddViewAJAX.as_view(), name='cart_addAJAX'),
]
