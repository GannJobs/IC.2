from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Record(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=300, default='')
    returned_arq = models.FileField
    created_at = models.DateField(auto_now_add=True)
    query_GPT = models.CharField(max_length=200)
    name_register = models.CharField(max_length=100)
