from django.db import models
import datetime


class DoorPassword(models.Model):
    password = models.CharField(max_length=5, primary_key=True)
    is_hard = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=None, blank=True, null=True)
    apply_time = models.DateTimeField(default=None, blank=True, null=True)
    due_time = models.DateTimeField(default=None, blank=True, null=True)
    description = models.CharField(max_length=200)


class DoorHistory(models.Model):
    action = models.CharField(max_length=50)
    # ['manual close','manual open','password open','auto close']
    time = models.DateTimeField(default=None, blank=True, null=True)
    # time when the action happened


class DoorDevices(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    #to identify devices
    status = models.BooleanField(default=False)
    # True if device are connected
    last_check = models.DateTimeField(default=None, blank=True, null=True)
