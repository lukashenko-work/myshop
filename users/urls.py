from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegister.as_view(), name='register'),
    path('login/', views.UserLogin.as_view(), name='login'),
    path('logout/', views.UserLogout.as_view(), name='logout'),
    path('forgot/', views.UserForgot.as_view(), name='forgot'),
    
]