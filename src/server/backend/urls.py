from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user/create', csrf_exempt(views.createuser), name='create_user'),
    path('user/login', csrf_exempt(views.auth_user), name='auth_user'),
    path('user/logout', csrf_exempt(views.logout_user), name='logout_user'),
    path('question/create', csrf_exempt(views.create_question), name='create_question'),
    path('question/assign/get', csrf_exempt(views.get_user_assignment), name='get_user_assignment'),
    path('question/assign/create', csrf_exempt(views.assign_user_questions), name='assign_questions')
]