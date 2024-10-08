from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Record(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=300, default='')
    arq = models.FileField(upload_to='data/')
    returned_arq = models.FileField(upload_to='data/')
    created_at = models.DateField(auto_now_add=True)