from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView
from django.views.generic.base import TemplateView

from core import settings
from orders.models import Order, OrderItem

from .cart import Cart
from .forms import CheckoutForm
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
        # products = Product.objects.all()
        # i = 1
        # for product in products:
        #     cart.add(product, i, override=True)
        #     i += 1
        # -----------------------
        context['cart'] = cart
        context['total'] = cart.get_total_price()
        return context


class CheckoutView(LoginRequiredMixin, View):
    """
    GET - /orders/checkout/ - показывает форму
    POST - /orders/checkout/ - создает заказ
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        cart = Cart(request)
        if len(cart) == 0:
            messages.error(request, 'Ваша корзина пуста')
            return redirect('orders:cart')

        form = CheckoutForm()
        total = cart.get_total_price()
        return render(request, 'orders/checkout.html', {
            'form': form,
            'cart': cart,
            'total': total
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        """Создание заказа"""
        cart = Cart(request)
        if len(cart) == 0:
            messages.error(request, 'Ваша корзина пуста')
            return redirect('orders:cart')

        form = CheckoutForm(request.POST)

        if not form.is_valid():
            return render(request, 'orders/checkout.html', {
                'form': form,
                'cart': cart,
                'total': cart.get_total_price()
            })

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                shipping_address=f"{form.cleaned_data['zip_code']}, {form.cleaned_data['city']}, {form.cleaned_data['address']}",
                # city=form.cleaned_data['city'],
                # zip_code=form.cleaned_data['zip_code'],
                comment=form.cleaned_data['comment'],
                total_price=cart.get_total_price(),
                status=Order.Status.PENDING,
            )

            for item in cart:
                product = item['product']
                qty = item['quantity']
                if product.stock < qty:
                    # Откат транзакции
                    raise ValueError(f'Недостаточно {product.name} на складе')

                OrderItem.objects.create(order=order, product=product, quantity=qty, price=item['price'])

                # Select for update
                Product.objects.filter(id=product.id).update(stock=product.stock - qty)

        cart.clear()

        self._send_confirmation_email(order)
        message = f"Заказ №{order.pk} успешно оформлен. Спасибо за покупку!"
        messages.success(request, message)

        return redirect('orders:success', order_id=order.pk)

    def _send_confirmation_email(self, order: Order) -> None:
        subject = f'Ваш заказ №{order.pk} в Hop & Barley'
        # message = f'Заказ №{order.pk} на сумму {order.total_price:.2f} успешно оформлен\n'
        message = (
            f'Здравствуйте, {order.full_name}.\n\n'
            f'Заказ №{order.pk} на сумму {order.total_price:.2f} успешно оформлен\n'
            f'Телефон: {order.phone_number}'
            f'Адрес доставки: {order.shipping_address}\nHop & Barley'
        )
        send_mail(subject, message, settings.FROM_EMAIL, [order.email])


class OrderSuccessView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/success.html"
    context_object_name = 'order'

    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
