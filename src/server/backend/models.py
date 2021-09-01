from django.db import models

# Create your models here.
class User(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.PositiveSmallIntegerField()
    username = models.CharField()
    password = models.CharField()