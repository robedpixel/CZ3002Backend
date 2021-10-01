import uuid

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Userassignment, Question, Result
from django.views.decorators.csrf import ensure_csrf_cookie
from django.forms.models import model_to_dict
from django.contrib.sessions.backends.db import SessionStore
import json, base64, pytz
from django.core import serializers
from datetime import datetime


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the backend index.")


@ensure_csrf_cookie
def createuser(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        sessionid = received_json_data['sessionid']
        session = SessionStore(session_key=sessionid)
        try:
            if session['role'] == 0:
                return HttpResponse("invalid permissions", status=400)
        except KeyError:
            return HttpResponse("Please log in to create accounts", status=400)
        current_role = int(session['role'])
        username = received_json_data['username']
        password = received_json_data['password']
        role = int(received_json_data['role'])
        try:
            displayname = received_json_data['displayname']
        except KeyError:
            displayname = None
        # if role < current_role or role == 2:
        if role < current_role or current_role == 2:
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
                    if displayname is not None:
                        saved_user.displayname = displayname
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
                s = SessionStore()
                s.create()
                s['authenticated'] = True
                s['uuid'] = str(database_acc_search[0].uuid)
                s['role'] = database_acc_search[0].role
                s.save()
                print(type(s.session_key))
                #request.session['authenticated'] = True
                #request.session['uuid'] = str(database_acc_search[0].uuid)
                #request.session['role'] = database_acc_search[0].role
                return JsonResponse(
                    {"userid": str(database_acc_search[0].uuid), "role": str(database_acc_search[0].role),
                     "sessionid": s.session_key},
                    status=200)
    return HttpResponse(status=400)


def logout_user(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                session.flush()
                return HttpResponse(status=200)
        except KeyError:
            return HttpResponse(status=400)


def get_info_user(request):
    if request.method == 'GET':
        try:
            sessionid = request.GET.get('sessionid')
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                user_uuid = request.GET.get('userid')
                saved_user = User.objects.filter(uuid=user_uuid).values()
                # Filter out password hash and role from the model before sending it
                response_list = []
                for user in saved_user:
                    diction = dict((key, value) for key, value in user.items() if
                                   key == 'username' or key == 'displayname')
                    response_list.append(diction)

                return JsonResponse({'users': response_list}, status=200)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def get_info_user_multi(request):
    if request.method == 'GET':
        try:
            sessionid = request.GET.get('sessionid')
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                if int(session['role']) >= 1:
                    users_role = request.GET.get('role')
                    saved_users = User.objects.filter(role=users_role).values()
                    response_list = []
                    # Filter out password hash and role from the model before sending it
                    for user in saved_users:
                        diction = dict((key, value) for key, value in user.items() if
                                       key == "uuid" or key == 'username' or key == 'displayname')
                        response_list.append(diction)

                    return JsonResponse({'users': response_list}, status=200)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


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
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated'] and int(session['role']) >= 1:
                userid = received_json_data['userid']
                database_uuid = User.objects.filter(uuid=userid)
                if not database_uuid:
                    return HttpResponse("no user found", status=400)
                questions = received_json_data['questions']
                difficulty = received_json_data['diffculty']
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
                    saved_assignment.difficulty = difficulty
                    saved_assignment.save()
                    return HttpResponse(status=201)
                else:
                    return HttpResponse("bad input", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def get_user_assignment(request):
    if request.method == 'GET':
        try:
            sessionid = request.GET.get('sessionid')
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                user_uuid = request.GET.get('userid')
                saved_assignment = Userassignment.objects.filter(userid=user_uuid)
                if saved_assignment:
                    # return json with questions ids

                    # Get list of ids from database
                    response = list(saved_assignment.values())
                    return JsonResponse({'assignments': response}, status=200)

                else:
                    return HttpResponse("user has no assigned questions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def start_user_assignment(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                assignment_id = received_json_data['assignmentid']
                saved_assignment = Userassignment.objects.filter(assignmentid=int(assignment_id))
                if saved_assignment:
                    # return json with questions ids

                    # Get list of ids from database
                    rand_token = uuid.uuid4()
                    saved_assignment[0].anstoken = rand_token
                    saved_assignment[0].save()
                    response = list(saved_assignment.values())
                    result = Result()
                    result.userid = saved_assignment[0].userid
                    result.attemptdatetime = pytz.utc.localize(datetime.now())
                    result.resultid = saved_assignment[0].assignmentid
                    result.save()
                    return JsonResponse({'assignments': response}, status=200)

                else:
                    return HttpResponse("user has no assigned questions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def complete_user_assignment(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                anstoken = received_json_data['anstoken']
                assignment_id = received_json_data['assignmentid']
                answers = received_json_data['answers']
                saved_assignment = Userassignment.objects.filter(assignmentid=int(assignment_id))
                if saved_assignment:
                    if saved_assignment[0].anstoken == uuid.UUID(anstoken):
                        questions = json.loads(saved_assignment[0].questions)
                        assignment_questions_list = []
                        correct_answers_list = []
                        for question in questions:
                            assignment_questions_list.append(int(question))
                        question_info = Question.objects.filter(questionid__in=assignment_questions_list)
                        for question in question_info:
                            correct_answers_list.append(int(question.answer))
                        # Add result to results
                        result = Result.objects.get(resultid=saved_assignment[0].assignmentid)
                        result.qnsanswered = len(assignment_questions_list)
                        qns_correct = 0
                        for ans, correct_ans in zip(answers, correct_answers_list):
                            if int(ans) == correct_ans:
                                qns_correct = qns_correct + 1
                        result.qnscorrect = qns_correct
                        result.completiontime = int((datetime.now() - result.attemptdatetime).total_seconds())
                        result.save()
                        # remove user assignment
                        saved_assignment[0].delete()
                        return HttpResponse(status=200)
                    else:
                        return HttpResponse("incorrect token sent", status=400)

                else:
                    return HttpResponse("user has no assigned questions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def get_question(request):
    if request.method == 'GET':
        try:
            sessionid = request.GET.get('sessionid')
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
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
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                if int(session['role']) >= 1:
                    saved_question = Question()
                    saved_question.save()
                    return HttpResponse(status=201)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def update_question(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                if int(session['role']) >= 1:
                    saved_question = Question()
                    response = {'updated': []}
                    try:
                        questionid = received_json_data['questionid']
                        searched_question = Question.objects.get(questionid=questionid)
                        if searched_question:
                            # Update all columns for all present params
                            question_updated = False

                            # Update for qnimg1
                            try:
                                qnimg1 = received_json_data['qnimg1']
                                if qnimg1:
                                    if qnimg1 == "DELETE":
                                        searched_question.qnimg1 = None

                                    else:
                                        searched_question.qnimg1 = base64.b64decode(qnimg1)
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
                                        searched_question.qnimg2 = None

                                    else:
                                        searched_question.qnimg2 = base64.b64decode(qnimg2)
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
                                        searched_question.answer = None
                                    else:
                                        searched_question.answer = bool(answer)
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
                                        searched_question.difficulty = None
                                        question_updated = True
                                    else:
                                        if 0 <= difficulty <= 32767:
                                            searched_question.difficulty = int(difficulty)
                                            response['updated'].append("difficulty")
                                            question_updated = True
                                        else:
                                            print("difficulty too large")
                                else:
                                    pass
                            except KeyError:
                                pass

                            if question_updated:
                                searched_question.save()
                                return JsonResponse(response, status=200)
                            return HttpResponse("no updates for question specified", status=200)
                    except KeyError:
                        return HttpResponse("no questionid specified!", status=400)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def get_question_multi(request):
    if request.method == 'GET':
        sessionid = request.GET.get('sessionid')
        session = SessionStore(session_key=sessionid)
        try:
            if session['authenticated']:
                difficulty = request.GET.get("difficulty")
                if difficulty:
                    int_difficulty = int(difficulty)
                    searched_question = Question.objects.filter(difficulty=int_difficulty)
                else:
                    searched_question = Question.objects.all()
                response = []
                for question in searched_question:
                    temp_dict_obj = model_to_dict(question)
                    temp_dict_obj['qnimg1'] = base64.b64encode(question.qnimg1).decode("utf-8")
                    temp_dict_obj['qnimg2'] = base64.b64encode(question.qnimg2).decode("utf-8")
                    response.append(temp_dict_obj)
                return JsonResponse({'questions': response}, status=200)
        except KeyError:
            return HttpResponse("Please Login", status=400)


def create_new_result(request):
    if request.method == 'POST':
        received_json_data = json.loads(request.body)
        sessionid = received_json_data['sessionid']
        session = SessionStore(session_key=sessionid)
        try:
            if session['authenticated']:
                if int(session['role']) >= 1:
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


def get_result_multi(request):
    if request.method == 'GET':
        sessionid = request.GET.get('sessionid')
        session = SessionStore(session_key=sessionid)
        try:
            if session['authenticated']:
                if int(session['role']) >= 1:
                    userid = request.GET.get('userid')
                    saved_result = Result.objects.filter(userid=userid)
                    if saved_result:
                        response = list(saved_result.values())
                        return JsonResponse({'results': response}, status=200)
                    return HttpResponse("results not found.", status=400)
                elif session['uuid'] == request.GET.get('userid'):
                    userid = request.GET.get('userid')
                    saved_result = Result.objects.filter(userid=userid)
                    if saved_result:
                        response = list(saved_result.values())
                        return JsonResponse({'results': response}, status=200)
                    return HttpResponse("results not found.", status=400)
                else:
                    return HttpResponse("Invalid permissions!", status=400)
        except KeyError:
            return HttpResponse("Please Login", status=400)
