from django.db import models
from django.db.models import Manager
# Импортируйте Review внутри TYPE_CHECKING, чтобы избежать циклического импорта
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reviews.models import Review


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Категория')
    slug = models.SlugField(max_length=200, verbose_name='URL-slug', unique=True)
    parent = models.ForeignKey(
        to='self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='children',
        verbose_name='Родительская категория'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=300, verbose_name='Название')
    slug = models.SlugField(max_length=300, verbose_name='URL-slug', unique=True)
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Вес')
    unit = models.CharField(max_length=20, verbose_name='Ед. измерения')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Категория')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    stock = models.PositiveIntegerField(default=0, verbose_name='Остаток')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Подсказка для Pylance:
    reviews: 'Manager[Review]'

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
