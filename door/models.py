from django.db import models
import datetime


class DoorPassword(models.Model):
    password = models.CharField(max_length=50)
    is_hard = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=None, blank=True, null=True)
    apply_time = models.DateTimeField(default=None, blank=True, null=True)
    due_time = models.DateTimeField(default=None, blank=True, null=True)
    description = models.CharField(max_length=200)


class DoorHistory(models.Model):
    action = models.CharField(max_length=50)
    time = models.DateField()
