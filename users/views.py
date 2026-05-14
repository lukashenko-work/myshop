from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import \
    url_has_allowed_host_and_scheme  # Для безопасности
from django.views import View
from django.views.generic import ListView

from orders.models import Order

from .forms import LoginForm, RegisterForm


class UserRegister(View):
    template_name = 'users/register.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('products:catalog')
        else:
            print(form.errors.as_data())
            return render(request, self.template_name, {'form': form})


class UserLogin(View):
    template_name = 'users/login.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if remember_me:
                    # Сессия будет жить долго (обычно 2 недели, настраивается в settings)
                    request.session.set_expiry(None)
                else:
                    # Сессия удалится сразу после закрытия вкладки/браузера
                    request.session.set_expiry(0)
                # 1. Забираем 'next' напрямую из POST запроса, игнорируя форму
                next_url = request.POST.get('next')

                # 2. Проверяем URL на безопасность (чтобы редирект был внутри нашего сайта)
                is_safe = url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                )
                # 3. Если 'next' есть и он безопасен — редиректим туда, иначе — в дефолтный каталог
                if next_url and is_safe:
                    return redirect(next_url)

                return redirect('products:catalog')
            else:
                form.add_error(None, "Неверный email или пароль")

        return render(request, self.template_name, {'form': form})


class UserLogout(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect('users:login')


class UserForgot(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        template_name = 'users/forgot_password.html'
        return render(request, template_name)

    def post(self, request: HttpRequest) -> HttpResponse:
        return redirect('users:login')


class UserOrderHistory(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'users/history.html'
    context_object_name = 'orders'
    paginate_by = 8

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).order_by('-created_at')
