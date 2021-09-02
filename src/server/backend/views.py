import uuid

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Userassignment
from django.views.decorators.csrf import ensure_csrf_cookie
import json

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the backend index.")


@ensure_csrf_cookie
def createuser(request):
    if request.method == 'POST':
        try:
            if request.session['role'] == 0:
                return HttpResponse("invalid permissions", status=400)
        except KeyError:
            return HttpResponse("Please log in to create accounts", status=400)
        current_role = int(request.session['role'])
        received_json_data=json.loads(request.body)
        username = received_json_data['username']
        password = received_json_data['password']
        role = received_json_data['role']
        if role < current_role or role == 2:
            if not User.objects.filter(username=username):
                if username is not None and password is not None and role is not None:
                    saved_user = User()
                    password_hash = make_password(password)
                    uuid_generated = False
                    while not uuid_generated:
                        user_uuid = uuid.uuid4()
                        database_uuid = User.objects.filter(users=user_uuid)
                        if not database_uuid:
                            saved_user.uuid = user_uuid
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
        received_json_data=json.loads(request.body)
        username = received_json_data['username']
        password = received_json_data['password']
        database_acc_search = User.objects.filter(username=username)
        if database_acc_search is not None:
            matchcheck = check_password(password, database_acc_search[0].password)
            if matchcheck:
                request.session['authenticated'] = True
                request.session['uuid'] = str(database_acc_search[0].uuid)
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

        
def get_user_questions(request):
    if request.method == 'GET':
        try:
            if request.session['authenticated']:
                print("test")
        except KeyError:
            return HttpResponse("Please Login", status = 400)
        user_uuid = request.session['uuid']
        database_assigned_questions = Userassignment()
        saved_assignment = database_assigned_questions.objects.filter(userid=user_uuid)
        if saved_assignment:
            #return json with questions ids
            print("test")
        else:
            return HttpResponse("user has no assigned questions!",status=400)
