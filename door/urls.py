# chat/urls.py
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views
from door.task import start_job

# start_job()

urlpatterns = [
    url(r'', views.dashboard),
]
