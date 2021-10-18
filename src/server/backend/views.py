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
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)

        try:
            if session['role'] == 0:
                return JsonResponse({"status": "Error:invalid permissions"}, status=400)
        except KeyError:
            return JsonResponse({"status": "Error:Please log in to create accounts"}, status=400)
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
                        return JsonResponse({"status": "Error:invalid role!"}, status=400)
                    saved_user.username = username
                    saved_user.password = password_hash
                    if displayname is not None:
                        saved_user.displayname = displayname
                    saved_user.save()
                    return JsonResponse({"status": "success"}, status=201)
                else:
                    return JsonResponse({"status": "error:bad user creation request"}, status=400)
            else:
                return JsonResponse({"status": "error:username already exists!"}, status=400)
        else:
            return JsonResponse({"status": "error:bad user creation request:invalid permissions"}, status=400)


def update_user_password(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            try:
                old_password = received_json_data['oldpassword']
                new_password = received_json_data['newpassword']
                if new_password is None:
                    return JsonResponse({"status": "error:missing params."}, status=400)
            except KeyError:
                return JsonResponse({"status": "error:missing params."}, status=400)
            saved_user = User.objects.get(uuid=session['uuid'])
            matchcheck = check_password(old_password, saved_user.password)
            if matchcheck:
                saved_user.password = make_password(new_password)
                saved_user.save()
                return JsonResponse({"status": "success"}, status=200)
            else:
                return JsonResponse({"status": "error:invalid password"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


def update_user_displayname(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            try:
                new_displayname = received_json_data['displayname']
            except KeyError:
                return JsonResponse({"status": "error:missing params."}, status=400)
            saved_user = User.objects.get(uuid=session['uuid'])
            saved_user.displayname = new_displayname
            saved_user.save()
            return JsonResponse({"status": "success"}, status=200)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
        if database_acc_search:
            matchcheck = check_password(password, database_acc_search[0].password)
            if matchcheck:
                s = SessionStore()
                s.create()
                s['authenticated'] = True
                s['uuid'] = str(database_acc_search[0].uuid)
                s['role'] = database_acc_search[0].role
                s.save()
                print(type(s.session_key))
                # request.session['authenticated'] = True
                # request.session['uuid'] = str(database_acc_search[0].uuid)
                # request.session['role'] = database_acc_search[0].role
                return JsonResponse(
                    {"status": "success", "userid": str(database_acc_search[0].uuid),
                     "role": str(database_acc_search[0].role),
                     "sessionid": s.session_key},
                    status=200)
            else:
                return JsonResponse(
                    {"status": "Error: invalid username or password"},
                    status=400)
        else:
            return JsonResponse(
                {"status": "Error: invalid username or password"},
                status=400)
    return JsonResponse({"status": "error"}, status=400)


def logout_user(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                session.flush()
                return JsonResponse({"status": "success"}, status=200)
        except KeyError:
            return JsonResponse({"status": "error"}, status=400)


def get_info_user(request):
    if request.method == 'GET':
        try:
            sessionid = request.GET.get('sessionid')
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                user_uuid = request.GET.get('userid')
                saved_user = User.objects.get(uuid=user_uuid)
                return JsonResponse(
                    {"status": "success", 'username': saved_user.username, 'displayname': saved_user.displayname},
                    status=200)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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

                    return JsonResponse({"status": "success", 'users': response_list}, status=200)
                else:
                    return JsonResponse({"status": "error:Invalid permissions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                try:
                    userid = received_json_data['userid']
                    questions = received_json_data['questions']
                    difficulty = received_json_data['difficulty']
                except KeyError:
                    return JsonResponse({"status": "error:missing params"}, status=400)
                database_uuid = User.objects.filter(uuid=userid)
                if not database_uuid:
                    return JsonResponse({"status": "error:no user found"}, status=400)
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
                    return JsonResponse({"status": "success"}, status=201)
                else:
                    return JsonResponse({"status": "error:bad input"}, status=400)
            else:
                return JsonResponse({"status": "error:invalid permissions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                    return JsonResponse({"status": "success", 'assignments': response}, status=200)

                else:
                    return JsonResponse({"status": "error:user has no assigned questions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                    result.difficulty = saved_assignment[0].difficulty
                    result.save()
                    return JsonResponse({"status": "success", 'assignments': response}, status=200)

                else:
                    return JsonResponse({"status": "error:user has no assigned questions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


def complete_user_assignment(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            try:
                anstoken = received_json_data['anstoken']
                assignment_id = received_json_data['assignmentid']
                answers = received_json_data['answers']
            except KeyError:
                return JsonResponse({"status": "error:missing params."}, status=400)
            if session['authenticated']:
                saved_assignment = Userassignment.objects.filter(assignmentid=int(assignment_id))
                if saved_assignment:
                    if saved_assignment[0].anstoken == uuid.UUID(anstoken):
                        questions = json.loads(saved_assignment[0].questions)
                        assignment_questions_list = []
                        correct_answers_list = []
                        for question in questions:
                            question_info = Question.objects.get(questionid=int(question))
                            correct_answers_list.append(int(question_info.answer))
                        # Add result to results
                        result = Result.objects.get(resultid=saved_assignment[0].assignmentid)
                        result.qnsanswered = len(questions)
                        qns_correct = 0
                        for ans, correct_ans in zip(answers, correct_answers_list):
                            if int(ans) == correct_ans:
                                qns_correct = qns_correct + 1
                        result.qnscorrect = qns_correct
                        result.completiontime = int((datetime.now() - result.attemptdatetime).total_seconds())
                        result.save()
                        # remove user assignment
                        saved_assignment[0].delete()
                        return JsonResponse({"status": "Success", "score": str(qns_correct)}, status=200)
                    else:
                        return JsonResponse({"status": "error:incorrect token sent"}, status=400)

                else:
                    return JsonResponse({"status": "error:user has no assigned questions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                return JsonResponse({"status": "error:no question found"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                    return JsonResponse({"status": "success", "questionid": str(saved_question.questionid)}, status=201)
                else:
                    return JsonResponse({"status": "error:Invalid permissions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


def update_question(request):
    if request.method == 'POST':
        try:
            received_json_data = json.loads(request.body)
            sessionid = received_json_data['sessionid']
            session = SessionStore(session_key=sessionid)
            if session['authenticated']:
                if int(session['role']) >= 1:
                    saved_question = Question()
                    response = {"status": "success", 'updated': []}
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
                            return JsonResponse({"status": "no updates for question specified"}, status=200)
                    except KeyError:
                        return JsonResponse({"status": "error:no questionid specified!"}, status=400)
                else:
                    return JsonResponse({"status": "error:Invalid permissions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                return JsonResponse({"status": "success", 'questions': response}, status=200)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


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
                        return JsonResponse({"status": "success"}, status=201)
                    return JsonResponse({"status": "error:userid not found."}, status=400)
                else:
                    return JsonResponse({"status": "error:Invalid permissions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)


def get_result_multi(request):
    if request.method == 'GET':
        sessionid = request.GET.get('sessionid')
        session = SessionStore(session_key=sessionid)
        try:
            if session['authenticated']:
                try:
                    userid = request.GET.get('userid')
                except KeyError:
                    return JsonResponse({"status": "error:missing params."}, status=400)
                if int(session['role']) >= 1:
                    saved_result = Result.objects.filter(userid=userid)
                    if saved_result:
                        response = list(saved_result.values())
                        return JsonResponse({"status": "success", 'results': response}, status=200)
                    return JsonResponse({"status": "error:results not found."}, status=400)
                elif session['uuid'] == request.GET.get('userid'):
                    saved_result = Result.objects.filter(userid=userid)
                    if saved_result:
                        response = list(saved_result.values())
                        return JsonResponse({"status": "success", 'results': response}, status=200)
                    return JsonResponse({"status": "error:results not found."}, status=400)
                else:
                    return JsonResponse({"status": "error:Invalid permissions!"}, status=400)
        except KeyError:
            return JsonResponse({"status": "error:Please Login"}, status=400)
