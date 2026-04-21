from typing import Any

from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic.base import TemplateView

from .cart import Cart
from products.models import Product


class CartAddView(View):
    def post(self, request: HttpRequest,  product_id: int):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = Cart(request)
        quantity = int(request.POST.get('quantity', 1))

        if quantity < 1 or quantity > product.stock:
            messages.error(request, message=f'Недопустимое количество. В наличии {product.stock} шт.')

        cart.add(product, quantity)
        messages.success(request, message=f'{product.name} добавлен в корзину')

        return redirect('orders:cart')


class CartRemoveView(View):
    def post(self, request: HttpRequest, product_id: int):
        cart = Cart(request)
        cart.remove(product_id)
        return redirect('orders:cart')


class CartView(TemplateView):
    template_name = 'orders/cart.html'

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)

        # TODO: Убрать этот код
        products = Product.objects.all()
        i = 1
        for product in products:
            cart.add(product, i, override=True)
            i += 1
        # -----------------------
        context['cart'] = cart
        context['total'] = cart.get_total_price()
        return context
