from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views import View

from .forms import RegisterForm


class UserRegister(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        template_name = 'users/register.html'
        form = RegisterForm()
        return render(request, template_name, {'form': form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('products:catalog')
        else:
            print(form.errors.as_data()) 
            return render(request, 'users/register.html', {'form': form})


class UserLogin(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        template_name = 'users/login.html'
        return render(request, template_name)


class UserLogout(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return redirect('users:login')


class UserForgot(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        template_name = 'users/forgot_password.html'
        return render(request, template_name)

    def post(self, request: HttpRequest) -> HttpResponse:
        return redirect('users:login')
