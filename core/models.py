from django.db import models
from django.utils import timezone

class UnixDateTImeField(models.DateTimeField):
    def pre_save(self, model_instance, add: bool) -> any:
        value = super().pre_save(model_instance, add)
        if isinstance(value,int):
            value = timezone.make_aware(timezone.datetime.fromtimestamp(value))
        return value

class User(models.Model):
    uid = models.CharField(max_length=1024,primary_key=True)
    email = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True,auto_now=False)
    
class Auth(models.Model):
    token = models.CharField(max_length=10240,primary_key=True)
    uid = models.CharField(max_length=1024)
    expired_at = UnixDateTImeField(auto_now=False,auto_now_add=False)
    
class Note(models.Model):
    class Meta:
        ordering = ['-updated_at']
        
    class NoteStatus(models.IntegerChoices):
        NORMAL = 1
        SOFT_DEL = -1
        HARD_DEL = -2
        
    id = models.CharField(max_length=1024,primary_key=True)
    uid = models.CharField(max_length=1024)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=NoteStatus.choices,default=NoteStatus.NORMAL)
    
class Client(models.Model):
    client_id = models.CharField(32,primary_key=True)
    uid = models.CharField(max_length=1024)
    client_type = models.CharField(max_length=32) # only web,app
    client_version = models.IntegerField() # eg 0.0.1 is 000001, web version always 000000
    os = models.CharField(32)
    created_at = models.DateTimeField(auto_now_add=True)