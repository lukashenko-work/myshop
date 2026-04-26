from typing import Any, cast

# from django.shortcuts import render
from django.db.models import F, Q, Avg, Count, QuerySet
from django.views.generic import DetailView, ListView

from orders.models import OrderItem

from .models import Category, Product


class ProductListView(ListView):
    model = Product
    template_name = 'products/catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self) -> QuerySet:
        qs = Product.objects.filter(is_active=True).select_related('category').annotate(
            avg_rating=Avg('reviews__rating'),
            # avg_rating=Coalesce(Avg('reviews__rating'), Value(0.0)))
            # Считаем количество связанных отзывов
            reviews_count=Count('reviews'))

        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        # Filter by search query if provided
        search_query = self.request.GET.get('q')

        if search_query:
            # qs = qs.filter(name__icontains=search_query) | qs.filter(description__icontains=search_query)
            qs = qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query)).distinct()

        # Filter by price range if provided
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        # Sorting, default new
        sort_by = self.request.GET.get('sort', 'new')
        sort_map = {
            'price_asc': (F('price').asc(), F('created_at').desc()),
            'price_desc': (F('price').desc(), F('created_at').desc()),
            # Сначала самые популярные (много отзывов), при совпадении — по рейтингу
            'popular': (F('reviews_count').desc(nulls_last=True), F('avg_rating').desc()),
            # Сначала высокие рейтинги, при совпадении — где больше отзывов
            'rating': (F('avg_rating').desc(nulls_last=True), F('reviews_count').desc()),
            'new': (F('created_at').desc(),)
        }

        order_rule = sort_map.get(sort_by, (sort_map['new']))
        qs = qs.order_by(*order_rule)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent=None).prefetch_related('children')
        # context['category_slug'] = self.kwargs.get('category_slug')
        context['current_category'] = self.request.GET.get('category')
        context['current_sort'] = self.request.GET.get('sort', 'new')
        context['current_q'] = self.request.GET.get('q')
        context['min_price'] = self.request.GET.get('min_price')
        context['max_price'] = self.request.GET.get('max_price')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(is_active=True).select_related('category')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product: Product = cast(Product, self.get_object())

        context['reviews'] = product.reviews.all().prefetch_related('user').order_by('-created_at')[:3]
        avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
        reviews_count = product.reviews.count()
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else None
        context['reviews_count'] = reviews_count
        context['max_rating'] = range(5)

        if self.request.user.is_authenticated:
            if OrderItem.objects.filter(product=product, order__user=self.request.user, order__status='completed').exists():
                context['can_review'] = True
            if product.reviews.filter(user=self.request.user).exists():
                context['already_reviewed'] = True

        # context['related_products'] = Product.objects.filter(category=product.category).exclude(pk=product.pk).prefetch_related('category')
        context['categories'] = Category.objects.filter(parent=None).prefetch_related('children')
        return context

# TODO: пейджинг, сток на карточке товаров, оставление отзыва и т.д.
