from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
import uuid

class SimpleUserManager(BaseUserManager):
    def create_user(self,email,**extra_fields):
        if not email:
            raise ValueError("Emails is required")
        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self,email,**extra_fields):
        return self.create_user(email,**extra_fields)

class UnixDateTImeField(models.DateTimeField):
    def pre_save(self, model_instance, add: bool) -> any:
        value = super().pre_save(model_instance, add)
        if isinstance(value,int):
            value = timezone.make_aware(timezone.datetime.fromtimestamp(value))
        return value

class User(AbstractBaseUser):
    id = models.CharField(max_length=1024,primary_key=True,default=uuid.uuid4,editable=False)
    email = models.CharField(max_length=128,unique=True)
    created_at = models.DateTimeField(auto_now_add=True,auto_now=False)
        
    objects = SimpleUserManager()
    
    USERNAME_FIELD = "email"
    
    
class Note(models.Model):
    class Meta:
        ordering = ['-updated_at']
        
    class NoteStatus(models.IntegerChoices):
        NORMAL = 1
        SOFT_DEL = -1
        HARD_DEL = -2
        
    id = models.CharField(max_length=1024,primary_key=True,default=uuid.uuid4,editable=False)
    uid = models.CharField(max_length=1024)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=NoteStatus.choices,default=NoteStatus.NORMAL)
    
class Client(models.Model):
    client_id = models.CharField(max_length=64,primary_key=True)
    uid = models.CharField(max_length=1024)
    client_type = models.CharField(max_length=32) # only web,app
    client_version = models.IntegerField() # eg 0.0.1 is 000001, web version always 000000
    os = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)