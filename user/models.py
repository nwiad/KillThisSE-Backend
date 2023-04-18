from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

import datetime

from utils.utils_time import *
from utils.utils_constant import MAX_CHAR_LENGTH, MAX_NAME_LENGTH


class User(AbstractBaseUser):
    user_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    USERNAME_FIELD = "name"
    
    avatar = models.CharField(max_length=MAX_CHAR_LENGTH, default="https://github.com/LTNSXD/LTNSXD.github.io/blob/main/img/favicon.jpg?raw=true")

    def serialize(self):
        return {
            "user_id": self.user_id, 
            "name": self.name, 
            "avatar": self.avatar
        }
    
    def __str__(self):
        return self.name


class Friendship(models.Model):
    user_id = models.IntegerField()
    friend_user_id = models.IntegerField()
    update_time = models.DateTimeField(default=datetime.datetime.now)  

    class Meta:
        unique_together = ('user_id', 'friend_user_id')


class FriendshipRequest(models.Model):
    user_id = models.IntegerField()
    friend_user_id = models.IntegerField()
    update_time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = ('user_id', 'friend_user_id')
