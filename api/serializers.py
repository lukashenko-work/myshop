from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from orders.cart import Cart
from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'stock', 'image', 'category']


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ProductListSerializer.Meta.fields + ['is_active', 'avg_rating', 'reviews_count', 'created_at', 'updated_at']

    def get_avg_rating(self, obj) -> float | None:
        reviews = Review.objects.filter(product=obj)
        # TODO: Померить скорость этих трех вариантов и варианта с annotate
        if reviews.exists():
            # return round(reviews.aggregate(avg=Avg('rating'))['avg'], 1)
            return round(sum([r.rating for r in reviews]) / len(reviews), 1)
        return None

        # avg_rating = obj.reviews.all().aggregate(avg=Avg('rating'))['avg']
        # return round(avg_rating, 1) if avg_rating else None

    def get_reviews_count(self, obj) -> int | None:
        return obj.reviews.count()  # Или ваша логика


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']

    def validate_rating(self, value):
        if not value or value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

    def validate_items(self, value):
        """
        value — это список данных, пришедших в поле 'items'
        """
        # 1. Проверяем, что список не пуст
        if not value:
            raise serializers.ValidationError("Список товаров не может быть пустым.")

        # 2. Опционально: проверяем, что нет дубликатов товаров в одном заказе
        product_ids = [item['product'].id for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Один и тот же товар указан несколько раз.")

        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'shipping_address', 'full_name', 'email',
                  'phone_number', 'comment', 'items', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    # Помечаем read_only, так как данные возьмем из сессии, а не из JSON
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'shipping_address', 'full_name', 'email',
                  'phone_number', 'comment', 'items']
        # Помечаем user как read_only, чтобы он не требовался в POST-запросе
        read_only_fields = ['user']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Системная ошибка: отсутствует контекст запроса.")
        cart = Cart(request)

        if len(cart) == 0:
            raise serializers.ValidationError("Ваша корзина пуста (Возможно истекла сессия).")

        # 1. Извлекаем список товаров из валидированных данных
        # validated_data уже не содержит 'items', так как мы сделали pop
        # items_data = validated_data.pop('items')

        # 2. Оборачиваем всё в транзакцию: если на каком-то товаре
        # произойдет ошибка, заказ не создастся вообще
        with transaction.atomic():
            # Создаем основной объект заказа (пока без total_price)
            order = Order.objects.create(**validated_data)
            total_sum = Decimal(0)

            # 2. Обрабатываем товары из сессии
            for item in cart:
                product_id = item['product'].id
                quantity = item['quantity']
                product = Product.objects.select_for_update().get(id=product_id)

                if product.stock < quantity:
                    raise serializers.ValidationError({
                        "items": f"Товара {product.name} недостаточно на складе. В наличии: {product.stock}"})

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=quantity
                )

                product.stock = F('stock') - quantity
                product.save()

                total_sum += product.price * quantity

            order.total_price = total_sum
            order.save()

            # 3. ОЧИЩАЕМ КОРЗИНУ в сессии после успешного заказа
            cart.clear()

        return order

    def update(self, instance, validated_data):
        # В PATCH-запросе для изменения данных заказа (адрес, телефон, коммент)
        # мы вообще не трогаем items, так как состав заказа уже определен.

        with transaction.atomic():
            # Обновляем только те текстовые поля, которые прислал фронтенд
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return instance


class UserRegisterSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True,  min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'])
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']


# для Session-based Cart:
class CartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
