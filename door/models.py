from django.db import models
from django.utils.timezone import now
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


# board status
class DoorDevices(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # to identify devices
    status = models.BooleanField(default=False)  # True if device are connected
    last_check = models.DateTimeField(default=None, blank=True, null=True)


class DoorState(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField(max_length=500)


# device's data logs
class DeviceStates(models.Model):
    id = models.CharField(max_length=10)
    state = models.IntegerField(default=0, blank=True, null=True)
    time = models.DateTimeField(default=now, primary_key=True)
