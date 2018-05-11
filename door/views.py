# chat/views.py
from django.shortcuts import render
from django.utils.safestring import mark_safe
from door.models import DoorPassword
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    password_list = DoorPassword.objects.all()
    args = {
        'password_list': password_list,
        'user': request.user
    }
    return render(request, 'dashboard.html',args)

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
