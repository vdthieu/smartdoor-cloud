# chat/views.py
from django.shortcuts import render
from django.utils.safestring import mark_safe
from door.models import DoorPassword, DoorHistory, DoorState
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib import auth

@login_required
def dashboard(request):
    password_list = DoorPassword.objects.all()
    history_list = DoorHistory.objects.all()
    auto = True if DoorState.objects.filter(key='auto')[0].value == 'on' else False
    args = {
        'password_list': password_list,
        'history_list': history_list,
        'user': request.user,
        'auto': auto
    }
    return render(request, 'dashboard.html', args)


def login(request):
    #if request.user.is_authenticated():
    #  return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            # correct username and password login the user
            auth.login(request, user)
            return redirect('/dashboard') 
        else:
            messages.error(request, 'Error wrong username/password')
    
    return render(request, 'registration/login.html')


def logout(request):
    auth.logout(request)
    return redirect('/login')
