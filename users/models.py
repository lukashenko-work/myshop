from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # full_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='ФИО')

    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    # zip_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='Почтовый индекс')
    # city = models.CharField(max_length=50, blank=True, null=True, verbose_name='Город')
    # shipping_address = models.TextField(verbose_name='Адрес доставки')

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    birthday = models.DateField(blank=True, null=True, verbose_name='Дата рождения')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        ordering = ['user']

    def __str__(self):
        return f'Пользователь {self.user.email}>'
