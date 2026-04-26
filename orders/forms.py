from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200, label='Получатель',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Иван Иванов'}))

    email = forms.EmailField(
        max_length=200, label='E-mail',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'example@mail.ru'}))

    phone_number = forms.CharField(
        max_length=20, label='Телефон',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': '+7 987 654 3210'}))

    zip_code = forms.CharField(
        max_length=20, label='Почтовый индекс',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': '123456'}))

    city = forms.CharField(
        max_length=100, label='Город',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Город'}))

    address = forms.CharField(
        max_length=200, label='Адрес',
        widget=forms.Textarea(attrs={'class': 'Textarea', 'placeholder': 'Адрес', 'rows': 3}))

    payment_method = forms.ChoiceField(
        choices=[
            ('card', 'Банковская карта'),
            ('wallet', 'Электронный кошелек'),
            ('cash', 'Наличные при получении'),],
        initial='cash',
        widget=forms.RadioSelect(attrs={'class': 'RadioSelect'}),
        label='Способ оплаты')

    comment = forms.CharField(
        max_length=200, label='Комментарий',
        widget=forms.Textarea(attrs={'class': 'Textarea', 'placeholder': 'Комментарий', 'rows': 4}))
