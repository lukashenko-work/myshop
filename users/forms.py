from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=100, label='E-mail', required=True,
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'example@mail.ru'}))


class RegisterForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=20, label='Телефон',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': '+7 987 654 3210'}))

    class Meta:
        model = User
        # Поля, которые Django запишет в стандартную таблицу User
        # в поле username будем записывать email
        fields = ("username", "email")

    def save(self, commit=True) -> User:
        # 1. Сохраняем пользователя (без записи в базу, если commit=False)
        user = super().save(commit=False)
        # Если хотим, чтобы email был логином, можно скопировать его в username
        user.email = self.cleaned_data['email']
        user.username = user.email

        if commit:
            user.save()
            # 2. Создаем или обновляем профиль (если сигналы не используются)
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone_number': self.cleaned_data['phone_number']  # ,
                    # 'address': self.cleaned_data['address']
                }
            )
        return user
