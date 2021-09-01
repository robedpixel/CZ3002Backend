from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('createuser', csrf_exempt(views.debug_createuser), name='create_user')
]