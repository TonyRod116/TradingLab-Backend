from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    profile_image = models.URLField(max_length=500, null=True, blank=True)


    def __str__(self):
        return self.username
