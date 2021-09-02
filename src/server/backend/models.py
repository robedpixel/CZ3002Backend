from django.db import models


# Create your models here.
class User(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False)
    role = models.PositiveSmallIntegerField()
    username = models.TextField()
    password = models.TextField()
    displayname = models.TextField()


class Question(models.Model):
    questionid = models.SmallAutoField(primary_key=True)
    qnimg1 = models.BinaryField()
    qnimg2 = models.BinaryField()
    answer = models.BooleanField()
    difficulty = models.PositiveSmallIntegerField()


class Userassignment(models.Model):
    userid = models.UUIDField(primary_key=True, editable=False)
    questions = models.TextField()
