from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user/create', csrf_exempt(views.createuser), name='create_user'),
    path('user/login', csrf_exempt(views.auth_user), name='auth_user'),
    path('user/logout', csrf_exempt(views.logout_user), name='logout_user'),
]