from decimal import Decimal

from django.http import HttpRequest

from products.models import Product

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self,  request: HttpRequest) -> None:
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product: Product, quantity: int = 1, override: bool = False):
        product_id = str(product.pk)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'name': product.name
            }

        if override:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Проверка остатка на складе
        max_qty = product.stock
        if self.cart[product_id]['quantity'] > max_qty:
            self.cart[product_id]['quantity'] = max_qty

        self.save()

    def remove(self, product_id: int):
        key = str(product_id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        del self.session[CART_SESSION_KEY]
        self.save()

    def get_total_price(self) -> Decimal:
        return sum(
            (Decimal(item['price']) * item['quantity']
                for item in self.cart.values()),
            Decimal('0')
        )

    def __iter__(self):
        product_ids = self.cart.keys()
        # Получаем товары и создаем словарь {id_строка: объект_Product}
        products = Product.objects.in_bulk(product_ids)

        for product_id, item in self.cart.items():
            # Создаем копию данных товара из сессии
            item_copy = item.copy()
            # Добавляем объект Product во ВРЕМЕННУЮ копию
            item_copy['product'] = products.get(int(product_id))
            # Считаем сумму (возвращаем Decimal, а не str, для удобства шаблона)
            item_copy['total_price'] = Decimal(item['price']) * item['quantity']
            yield item_copy

    # def __iter__(self):
    #     product_ids = self.cart.keys()
    #     products = Product.objects.filter(id__in=product_ids)
    #     cart = self.cart.copy()
    #     for product in products:
    #         cart[str(product.pk)]['product'] = product
    #     for item in cart.values():
    #         item['total_price'] = str(Decimal(item['price']) * item['quantity'])
    #         yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
