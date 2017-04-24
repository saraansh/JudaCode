from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from judge.models import Users, Problems, Solve
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
import json

# Create your views here.
def index(request):
    try:
        if request.session['username']:
            return render(request, 'users/index.html')
        else:
            return render(request, 'users/login.html')
    except KeyError:
        return render(request, 'users/login.html')

def users_index(request):
    try:
        if request.session['username']:
            return HttpResponseRedirect("/judge")
        else:
            return render(request, 'users/login.html')
    except KeyError:
        return render(request, 'users/login.html')

def admin_index(request):
    try:
        if request.session['username']:
            if request.session['username']=='admin':
                return HttpResponseRedirect("newprob/")
            else:
                del request.session['username']
                del request.session['password']
                logout(request)
                return render(request, 'admin_site/index.html', {'error': 2})
        else:
            return render(request, 'admin_site/index.html', {'error': 2})
    except KeyError:
        context = RequestContext(request)
        error = 1
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            if username=='admin' and password=='pclub2014dhpc':
                request.session['username']  = username
                request.session['password']  = password
                return HttpResponseRedirect("/judge/admin_site/newprob/")
            else:
                error = 1
        else:
            error = 2
        return render(request, 'admin_site/index.html', {'error': error})

def newprob(request):
    try:
        if request.session['username']:
            if request.session['username']=='admin':
                return render(request, 'admin_site/newprob.html')
            else:
                return HttpResponseRedirect("/judge/admin_site/")
        else:
            return HttpResponseRedirect("/judge/admin_site/")
    except KeyError:
        return HttpResponseRedirect("/judge/admin_site/")

def adminlogout(request):
    try:
        if request.session['username']:
            del request.session['username']
        return HttpResponseRedirect("/judge/admin_site/")
    except KeyError:
        return HttpResponseRedirect("/judge/admin_site/")

def adminsubmit(request):
    try:
        if request.session['username']:
            if request.session['username']=='admin':
                context = RequestContext(request)
                if request.method == 'POST':
                    probname = request.POST['probname']
                    probstat = request.POST['probstat']
                    testin = request.POST['testin']
                    testout = request.POST['testout']
                    points = request.POST['points']
                    timelimit = request.POST['timelimit']
                    query = Problems.objects.filter(problem_name=probname)
                    if query:
                        return render(request, 'admin_site/newprob.html', {'error': 1})
                    else:
                        problem = Problems.objects.create(problem_name=probname, problem_statement=probstat, input=testin, solvedby=0, output=testout, points=points, time=timelimit)
                        problem.save()
                    return render(request, 'admin_site/newprob.html', {'error': 2})
                else:
                    return render(request, 'admin_site/newprob.html', {'error': 3})
            else:
                return HttpResponseRedirect("/judge/admin_site/logout/")
        else:
            return HttpResponseRedirect("/judge/admin_site/")
    except KeyError:
        return HttpResponseRedirect("/judge/admin_site/")


def register(request):
    context = RequestContext(request)
    errors = False
    if request.method == 'POST' and request.is_ajax():
        username = request.POST['user_name']
        password = request.POST['pass_word']
        email = request.POST['email']
        query = User.objects.filter(username=username)
        if query:
            errors = True
        else:
            user = User.objects.create_user(username, email, password)
            user.save()
            query = Users.objects.create(username = username)
            query.save()
            user = authenticate(username=username, password=password)
            login(request, user)
            request.session['username']  = username
            request.session['password']  = password
            print(request.session['username'])

        return HttpResponse(json.dumps({'errors': errors}),content_type='application/json')
    else:
        raise Http404


def user_login(request):
    try:
        if request.session['username']:
            return HttpResponseRedirect("/judge")
    except KeyError:
        context = RequestContext(request)
        error = False
        if request.method == 'POST' and request.is_ajax():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user != None:
                if user.is_authenticated():
                    login(request, user)
                    request.session['username']  = username
                    request.session['password']  = password
                    return HttpResponse(json.dumps({'errors': error}),content_type='application/json')
                else:
                    error = True
                    return HttpResponse(json.dumps({'errors': error}),content_type='application/json')
            else:
                error = True
                return HttpResponse(json.dumps({'errors': error}),content_type='application/json')

        return render(request, 'users/login.html')


@login_required
def usersubmit(request, problem_id):
    prob = get_object_or_404(Problems, id=problem_id)
    context = RequestContext(request)
    if request.method == 'POST':
        username = request.session['username']
        language = request.POST['language']
        code = request.POST['code']
        status = False
        # send for judging and retrieve results
        # status = True (For correct solution)
        # If AC, increment user's solved, score and problem's solvedby
        query_for_getting_user = Users.objects.get(username=username)
        try:
            query = Solve.objects.get(username=username, problem_id=prob.id)
        except Solve.DoesNotExist:
            query = None

        if(query and not query.status):
            prob.solvedby = prob.solvedby+1
            query_for_getting_user.solved = query_for_getting_user.solved+1
            query_for_getting_user.score = query_for_getting_user.score + prob.points
            query_for_getting_user.save()
            prob.save()
        if(query):
            # increment attempts and change status accordingly
            query.attempts = query.attempts+1
            query.status = status
            query.solution = code
            if status:
                query.score = prob.points
            query.save()
        else:
            # New entry
            if status:
                query_for_creating_newEntry = Solve.objects.create(problem_id = prob.id, score=prob.points, username = username, status = status, solution = code, language = language, attempts=1)
            else:
                query_for_creating_newEntry = Solve.objects.create(problem_id = prob.id, score=0, username = username, status = status, solution = code, language = language, attempts=1)
            query_for_creating_newEntry.save()
    if status:
        return render(request, 'problems/details.html', {'prob': prob, 'status': True})
    else:
        return render(request, 'problems/details.html', {'prob': prob, 'status': False})

@login_required
def change_password(request):
    error = 0
    if request.method == "POST":
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        user = authenticate(username=request.session['username'], password=old_password)
        if user is not None:
            query = User.objects.get(username=request.session['username'])
            query.set_password(new_password)
            query.save()
            error = 1
            t = loader.get_template('users/account.html')
            c = RequestContext(request, {'error': error})
            return HttpResponse(t.render(c))
        else:
            error = 2
            t = loader.get_template('users/account.html')
            c = RequestContext(request, {'error': error})
            return HttpResponse(t.render(c))


@login_required
def change_email(request):
    error = 3
    if request.method == "POST":
        email = request.POST['email']
        query = User.objects.get(username=request.session['username'])
        query.email = email
        query.save()
        error = 4
    t = loader.get_template('users/account.html')
    c = RequestContext(request, {'error': error})
    return HttpResponse(t.render(c))

@login_required
def user_logout(request):
    del request.session['username']
    del request.session['password']
    logout(request)
    return HttpResponseRedirect("/judge/login")

@login_required
def leaderboard(request):
    users = Users.objects.order_by('score')
    return render(request, 'users/leaderboard.html', {'users': users})

@login_required
def submissions(request):
    solutions = Solve.objects.order_by('time')
    return render(request, 'users/submissions.html', {'solutions': solutions})

@login_required
def account(request):
    return render(request, 'users/account.html')

@login_required
def problems(request):
    problems = Problems.objects.order_by('id')
    return render(request, 'problems/index.html', {'problems': problems})

@login_required
def details(request, problem_id):
    prob = get_object_or_404(Problems, id=problem_id)
    try:
        solution = Solve.objects.get(username=request.session['username'], problem_id=prob.id)
    except Solve.DoesNotExist:
        solution = None
    status = False
    if solution:
        if solution.status==1:
            status = True
    return render(request, 'problems/details.html', {'prob': prob, 'status': status})
