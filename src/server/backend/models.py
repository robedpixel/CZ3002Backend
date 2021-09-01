from django.db import models


# Create your models here.
class User(models.Model):
    users = models.UUIDField(primary_key=True, editable=False)
    role = models.PositiveSmallIntegerField()
    username = models.TextField()
    password = models.TextField()
