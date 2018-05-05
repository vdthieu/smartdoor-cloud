# chat/views.py
from django.shortcuts import render
from django.utils.safestring import mark_safe
from door.models import DoorPassword
import json


def dashboard(request):
    password_list = DoorPassword.objects.all()
    return render(request, 'dashboard.html', {
        'password_list': password_list
    })
