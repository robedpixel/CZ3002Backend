from django.db import models


# Create your models here.
class User(models.Model):
    users = models.UUIDField(primary_key=True, editable=False)
    role = models.PositiveSmallIntegerField()
    username = models.TextField()
    password = models.TextField()


class Question(models.Model):
    questionid = models.SmallAutoField(primary_key=True)
    qnimg = models.BinaryField()
    qnansimg1 = models.BinaryField()
    qnansimg2 = models.BinaryField()
    qnansimg3 = models.BinaryField()
    qnansimg4 = models.BinaryField()


class Userassignment(models.Model):
    userid = models.UUIDField(primary_key=True, editable=False)
    questions = models.TextField()
