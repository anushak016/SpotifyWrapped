from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('reset_password/', views.request_username_view, name='request_username'),
    path('reset_password/security_question', views.reset_password_view, name='reset_password'),
    path('login_user/<str:username>/', views.login_user, name='login_user'),
]