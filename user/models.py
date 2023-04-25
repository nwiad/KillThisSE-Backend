from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

import datetime

from utils.utils_time import *
from utils.utils_constant import MAX_CHAR_LENGTH, MAX_NAME_LENGTH

# 用户管理
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

# 好友关系
class Friendship(models.Model):
    user_id = models.IntegerField()
    friend_user_id = models.IntegerField()
    update_time = models.DateTimeField(default=datetime.datetime.now)  

    class Meta:
        unique_together = ('user_id', 'friend_user_id')

# 好友关系
class FriendshipRequest(models.Model):
    user_id = models.IntegerField()
    friend_user_id = models.IntegerField()
    update_time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = ('user_id', 'friend_user_id')
        
        
# 群组
class Group(models.Model):
    group_id = models.IntergerField() # group id
    group_name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True) # group name
    admin_id = models.IntegerField()  # group admin
    update_time = models.DateTimeField(default=datetime.datetime.now)  # update time
    
    class Meta:
        unique_together = ('group_id', 'group_name')
    
# 群组成员和分组id的绑定关系
class GroupFriend(models.Model):
    group_id = models.IntergerField() # group id
    user_id = models.IntegerField()  # user id
    update_time = models.DateTimeField(default=datetime.datetime.now)  # update time
    
    class Meta:
        unique_together = ('group_id', 'user_id')
    
