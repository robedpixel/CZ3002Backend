import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from .models import User
from django.views.decorators.csrf import ensure_csrf_cookie


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@ensure_csrf_cookie
def debug_createuser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        if not User.objects.filter(username=username):
            if username is not None and password is not None and role is not None:
                saved_user = User()
                password_hash = make_password(password)
                uuid_generated = False
                while not uuid_generated:
                    user_uuid = uuid.uuid4()
                    database_uuid = User.objects.filter(users=user_uuid)
                    if not database_uuid:
                        saved_user.users = user_uuid
                        uuid_generated = True

                saved_user.role = int(role)
                saved_user.username = username
                saved_user.password = password_hash
                saved_user.save()
                return HttpResponse(status=201)
            else:
                return HttpResponse("bad user creation request",status=400)
        else:
            return HttpResponse("username already exists!", status=400)
