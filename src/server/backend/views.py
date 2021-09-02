import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import User
from django.views.decorators.csrf import ensure_csrf_cookie


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@ensure_csrf_cookie
def createuser(request):
    if request.method == 'POST':
        try:
            if request.session['role'] == 0:
                return HttpResponse("invalid permissions", status=400)
        except KeyError:
            return HttpResponse("Please log in to create accounts", status=400)
        currentrole = int(request.session['role'])
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        if role < currentrole or role == 2:
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
                    return HttpResponse("bad user creation request", status=400)
            else:
                return HttpResponse("username already exists!", status=400)
        else:
            return HttpResponse("bad user creation request:invalid permissions", status = 400)
            

def auth_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        database_acc_search = User.objects.filter(username=username)
        if database_acc_search is not None:
            matchcheck = check_password(password, database_acc_search[0].password)
            if matchcheck:
                request.session['authenticated'] = True
                request.session['username'] = username
                request.session['role'] = database_acc_search[0].role
                return HttpResponse(status=200)
    return HttpResponse(status=400)


def logout_user(request):
    if request.method == 'POST':
        try:
            if request.session['authenticated']:
                request.session.flush()
                return HttpResponse(status=200)
        except KeyError:
            return HttpResponse(status=400)
