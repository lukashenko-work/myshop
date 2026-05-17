from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializers import (OrderCreateSerializer, OrderSerializer,
                             ProductDetailSerializer, ProductListSerializer,
                             ReviewSerializer, UserRegisterSerializer)
from orders.cart import Cart
from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """_summary_
    GET /api/products/ - список товаров с пагинацией фильтрацией и поиском list
    GET /api/products/{id}/ - детали товара, включает средний рейтинг, количество отзывов, список отзывов retrieve

    Args:
        viewsets (_type_): _description_
    """
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('reviews')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'price', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    # api/v1/products/reviews/
    @action(detail=True, methods=['get', 'post'], url_path='reviews', permission_classes=[AllowAny,])
    def reviews(self, request, *args, **kwargs):
        product = self.get_object()
        if request.method == 'GET':
            reviews = Review.objects.filter(product=product)
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response(data={'detail': 'You must be logged in to review a product.'}, status=status.HTTP_401_UNAUTHORIZED)

        bought = OrderItem.objects.filter(order__user=request.user, product=product, order__status=Order.Status.DELIVERED).exists()
        if not bought:
            return Response(data={'detail': 'You can only review products you have purchased.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False)
    def top(self, request):
        products = self.queryset.order_by('-rating__avg')[:5]
        return Response(ProductListSerializer(products, many=True).data)


class OrderViewSet(viewsets.ModelViewSet):
    """_summary_
    GET /api/orders/ - список заказов пользователя
    POST /api/orders/ - создание нового заказа
    GET /api/orders/{id}/ - детали заказа
    PATCH /api/orders/<int:id>/ - обновление заказа
    DELETE /api/orders/<int:id>/ - удаление заказа

    # PUT вызывает метод update().PATCH вызывает тот же update(), но с флагом partial=True.

    Args:
        viewsets (_type_): _description_
    """
    # Базовый queryset (здесь можно указать общие правила для всех)
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']  # заказы не удаляем, просто отменяем

    def get_serializer_class(self):
        # Если создаем — используем "создающий", иначе — "детальный"
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        # 1. Берем базу
        # 2. Ограничиваем владельцем
        # 3. Ускоряем загрузку связанных данных
        return super().get_queryset().filter(user=self.request.user).prefetch_related('items__product')

    # Переопределяем только этот метод, чтобы "подмешать" юзера
    def perform_create(self, serializer):
        # Это вызовет метод create() в OrderCreateSerializer
        # и добавит туда пользователя
        serializer.save(user=self.request.user)
        # Метод create() писать НЕ НУЖНО.
        # DRF сам возьмет его из базового класса и вызовет perform_create внутри.

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None) -> Response:
        """Отменяет заказ
        POST /api/orders/{id}/cancel/

        Args:
            request (_type_): _description_
            pk (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        order = self.get_object()

        # 1. Проверяем, можно ли вообще отменить заказ
        if order.status in [Order.Status.DELIVERED, Order.Status.CANCELLED, Order.Status.SHIPPED, Order.Status.COMPLETED]:
            return Response(
                {'error': f'Нельзя отменить заказ в статусе {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Проводим отмену атомарно
        with transaction.atomic():
            # Возвращаем товары на склад
            for item in order.items.all():
                if item.product:  # Если товар еще существует в базе
                    item.product.stock = F('stock') + item.quantity
                    item.product.save()

            # Меняем статус
            order.status = Order.Status.CANCELLED
            order.save()

        return Response({'status': 'Заказ успешно отменен'})


class CartAPIView(generics.GenericAPIView):
    def get(self, request):
        cart = Cart(request)
        data = []

        for item in cart:
            data.append({
                'product_id': item['product'].id,
                'name': item['product'].name,
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['quantity'] * item['price']
            })

        return Response({'items': data, 'total': cart.get_total_price()})

    def post(self, request):
        product_id = request.data.get('product_id')
        # 1. Проверяем обязательное поле product_id
        if not product_id:
            raise ValidationError({'product_id': 'Это поле обязательно.'})

        # 2. Безопасно получаем и проверяем количество
        try:
            quantity = int(request.data.get('quantity', 1))
            if quantity <= 0:
                raise ValueError
        except (TypeError, ValueError):
            raise ValidationError({'quantity': 'Количество должно быть целым положительным числом.'})

        # 3. Находим товар в базе (если не найден — вернет 404)
        product = get_object_or_404(Product, id=product_id)

        cart = Cart(request)
        cart.add(product=product, quantity=quantity)

        return Response({'status': 'Товар добавлен в корзину'}, status=status.HTTP_200_OK)

    def delete(self, request):
        product_id = request.data.get('product_id')
        # 1. Проверяем обязательное поле product_id
        if not product_id:
            raise ValidationError({'product_id': 'Это поле обязательно.'})

        # 2. Находим товар в базе (если не найден — вернет 404)
        product = get_object_or_404(Product, id=product_id)

        cart = Cart(request)
        cart.remove(product.pk)

        return Response({'status': f'Товар {product.name} удален из корзины'}, status=status.HTTP_200_OK)


class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
