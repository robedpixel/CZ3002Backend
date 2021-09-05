import uuid

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Userassignment, Question, Result
from django.views.decorators.csrf import ensure_csrf_cookie
from django.forms.models import model_to_dict
import json, base64


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


def create_user_assignment(request):
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


def get_user_assignment(request):
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


def get_question(request):
    if request.method == 'GET':
        try:
            if request.session['authenticated']:
                questionid = request.GET.get("questionid")
                if questionid:
                    searched_question = Question.objects.filter(questionid=questionid)
                    if searched_question:
                        saved_question = searched_question[0]
                        temp_dict_obj = model_to_dict(saved_question)
                        temp_dict_obj['qnimg1'] = base64.b64encode(saved_question.qnimg1).decode("utf-8")
                        temp_dict_obj['qnimg2'] = base64.b64encode(saved_question.qnimg2).decode("utf-8")
                        return JsonResponse(temp_dict_obj, status=200)
                return HttpResponse("no question found", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def create_question(request):
    if request.method == 'POST':
        try:
            if request.session['authenticated']:
                if int(request.session['role']) >= 1:
                    saved_question = Question()
                    saved_question.save()
                    return HttpResponse(status=200)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def update_question(request):
    if request.method == 'POST':
        try:
            if request.session['authenticated']:
                if int(request.session['role']) >= 1:
                    received_json_data = json.loads(request.body)
                    saved_question = Question()
                    response = {}
                    response['updated'] = []
                    try:
                        questionid = received_json_data['questionid']
                        searched_question = Question.objects.filter(questionid=questionid)
                        if searched_question:
                            # Update all columns for all present params
                            question_updated = False
                            saved_question.questionid = questionid

                            # Update for qnimg1
                            try:
                                qnimg1 = received_json_data['qnimg1']
                                if qnimg1:
                                    if qnimg1 == "DELETE":
                                        saved_question.qnimg1 = None

                                    else:
                                        saved_question.qnimg1 = base64.b64decode(qnimg1)
                                    response['updated'].append("qnimg1")
                                    question_updated = True
                                else:
                                    pass
                            except KeyError:
                                pass

                            # Update for qnimg2
                            try:
                                qnimg2 = received_json_data['qnimg2']
                                if qnimg2:
                                    if qnimg2 == "DELETE":
                                        saved_question.qnimg2 = None

                                    else:
                                        saved_question.qnimg2 = base64.b64decode(qnimg2)
                                    response['updated'].append("qnimg2")
                                    question_updated = True
                                else:
                                    pass
                            except KeyError:
                                pass

                            # Update for answer
                            try:
                                answer = received_json_data['answer']
                                if answer:
                                    if answer == "DELETE":
                                        saved_question.answer = None
                                    else:
                                        saved_question.answer = bool(answer)
                                    response['updated'].append("answer")
                                    question_updated = True
                                else:
                                    pass
                            except KeyError:
                                pass

                            # Update for difficulty
                            try:
                                difficulty = received_json_data['difficulty']
                                if difficulty:
                                    if difficulty == "DELETE":
                                        saved_question.difficulty = None
                                        question_updated = True
                                    else:
                                        if 0 <= difficulty <= 32767:
                                            saved_question.difficulty = int(difficulty)
                                            response['updated'].append("difficulty")
                                            question_updated = True
                                        else:
                                            print("difficulty too large")
                                else:
                                    pass
                            except KeyError:
                                pass

                            if question_updated:
                                saved_question.save()
                                return JsonResponse(response, status=200)
                            return HttpResponse("no updates for question specified", status=200)
                    except KeyError:
                        return HttpResponse("no questionid specified!", status=400)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def create_new_result(request):
    if request.method == 'POST':
        try:
            if request.session['authenticated']:
                if int(request.session['role']) >= 1:
                    received_json_data = json.loads(request.body)
                    saved_result = Result()
                    userid = received_json_data['userid']
                    saved_assignment = Userassignment.objects.filter(userid=userid)
                    if saved_assignment:
                        saved_result.userid = userid
                        saved_result.save()
                        return HttpResponse(status=201)
                    return HttpResponse("userid not found.", status=400)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)
