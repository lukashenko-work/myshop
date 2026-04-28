from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=100, label='Email', required=True,
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'example@mail.ru'}))

    password = forms.CharField(
        label='Пароль', required=True,
        widget=forms.PasswordInput(attrs={'class': 'Input', 'placeholder': 'Пароль'}))

    remember_me = forms.BooleanField(
        required=False, label='Remember me', initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'Checkbox'}))


class RegisterForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=20, label='Телефон',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': '+7 987 654 3210'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Словарь: ключ — это имя поля в fields, значение — текст подсказки

        # Словарь соответствий: 'имя_поля': ('Label', 'Placeholder')
        field_data = {
            'username': ('Логин', 'Username'),
            'email': ('Email', 'example@mail.ru'),
            'password1': ('Пароль', 'Пароль'),
            'password2': ('Подтвердите пароль', 'Повторите пароль'),
            'phone_number': ('Телефон', '+7 900 000 00 00'),
        }
        # Самый быстрый способ добавить класс ВСЕМ полям сразу:
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'Input'
            # Обновляем Label и Placeholder, если они есть в словаре
            if field_name in field_data:
                label_text, placeholder_text = field_data[field_name]
                field.label = label_text
                field.widget.attrs['placeholder'] = placeholder_text

    class Meta:
        model = User
        # Поля, которые Django запишет в стандартную таблицу User
        # в поле username будем записывать email
        fields = ("username", "email", "phone_number")

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
