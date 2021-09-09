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
    assignmentid = models.AutoField(primary_key=True, editable=False)
    userid = models.UUIDField(editable=False)
    questions = models.TextField()
    anstoken = models.UUIDField()


class Result(models.Model):
    resultid = models.IntegerField(primary_key=True, editable=False)
    userid = models.UUIDField(editable=False)
    qnsanswered = models.IntegerField()
    qnscorrect = models.IntegerField()
    attemptdatetime = models.DateTimeField()
    completiontime = models.IntegerField()

    class Meta:
        unique_together = (('resultid', 'userid'),)
