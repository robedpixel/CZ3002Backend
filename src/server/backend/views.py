import uuid

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Userassignment, Question
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
        received_json_data = json.loads(request.body)
        current_role = int(request.session['role'])
        username = received_json_data['username']
        password = received_json_data['password']
        role = int(received_json_data['role'])
        if role < current_role or role == 2:
            if not User.objects.filter(username=username):
                if username is not None and password is not None and role is not None:
                    saved_user = User()
                    password_hash = make_password(password)
                    uuid_generated = False

                    # Generate for uuid and check if it already exists, if it does generate a new one
                    while not uuid_generated:
                        user_uuid = uuid.uuid4()
                        database_uuid = User.objects.filter(uuid=user_uuid)
                        if not database_uuid:
                            saved_user.uuid = user_uuid
                            uuid_generated = True
                    # Verify that the role is valid
                    if 0 <= role <= 2:
                        saved_user.role = role
                    else:
                        return HttpResponse("invalid role!", status=400)
                    saved_user.username = username
                    saved_user.password = password_hash
                    saved_user.save()
                    return HttpResponse(status=201)
                else:
                    return HttpResponse("bad user creation request", status=400)
            else:
                return HttpResponse("username already exists!", status=400)
        else:
            return HttpResponse("bad user creation request:invalid permissions", status=400)


def debug_create_user(request):
    received_json_data = json.loads(request.body)
    username = received_json_data['username']
    password = received_json_data['password']
    role = int(received_json_data['role'])
    if not User.objects.filter(username=username):
        if username is not None and password is not None and role is not None:
            saved_user = User()
            password_hash = make_password(password)
            uuid_generated = False
            while not uuid_generated:
                user_uuid = uuid.uuid4()
                database_uuid = User.objects.filter(uuid=user_uuid)
                if not database_uuid:
                    saved_user.uuid = user_uuid
                    uuid_generated = True
            if 0 <= role <= 2:
                saved_user.role = role
            else:
                return HttpResponse("invalid role!", status=400)
            saved_user.username = username
            saved_user.password = password_hash
            saved_user.save()
            return HttpResponse(status=201)
        else:
            return HttpResponse("bad user creation request", status=400)
    else:
        return HttpResponse("username already exists!", status=400)


def auth_user(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
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


def debug_check_auth(request):
    if request.method == 'POST':
        try:
            if request.session['authenticated']:
                return HttpResponse(status=200)
        except ValueError:
            return HttpResponse(status=400)


def assign_user_questions(request):
    if request.method == 'POST':
        try:
            if request.session['authenticated'] and int(request.session['role']) >= 1:
                received_json_data = json.loads(request.body)
                if received_json_data:
                    saved_user = User()
                    userid = received_json_data['userid']
                    database_uuid = User.objects.filter(uuid=userid)
                    if not database_uuid:
                        return HttpResponse("no user found", status=400)
                    questions = received_json_data['questions']
                    print(questions)
                    # verify if input is reasonable
                    verified = True
                    for row in questions:
                        if not row.isnumeric():
                            verified = False
                    if verified:
                        saved_assignment = Userassignment()
                        saved_assignment.userid = userid
                        saved_assignment.questions = json.dumps(questions)
                        saved_assignment.save()
                        return HttpResponse(status=200)
                    else:
                        return HttpResponse("bad input", status=400)
                else:
                    return HttpResponse("bad input", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def get_user_questions(request):
    if request.method == 'GET':
        try:
            if request.session['authenticated']:
                user_uuid = request.GET.get('userid')
                saved_assignment = Userassignment.objects.filter(userid=user_uuid)
                if saved_assignment:
                    # return json with questions ids

                    # Get list of ids from database
                    questions = json.loads(saved_assignment[0].questions)
                    json_data = {}
                    json_data['questions'] = questions
                    return JsonResponse(json_data, status=200)

                else:
                    return HttpResponse("user has no assigned questions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)
