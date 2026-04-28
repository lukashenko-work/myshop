from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views import View

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
        print('get')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request: HttpRequest) -> HttpResponse:
        print('post')
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')

            user = authenticate(request, username=email, password=password)
            print(user)
            if user is not None:
                login(request, user)
                if remember_me:
                    # Сессия будет жить долго (обычно 2 недели, настраивается в settings)
                    print(1)
                    request.session.set_expiry(None)
                else:
                    # Сессия удалится сразу после закрытия вкладки/браузера
                    print(2)
                    request.session.set_expiry(0)
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
