# chat/urls.py
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views
from door.task import start_job
from django.shortcuts import redirect
start_job()

urlpatterns = [
    #url(r'', views.dashboard),
    url(r'^dashboard/', views.dashboard),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='login')
]
