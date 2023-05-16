from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import random
import datetime

from utils.utils_time import *
from utils.utils_constant import MAX_CHAR_LENGTH, MAX_NAME_LENGTH

default_avatars = [
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A41.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A42.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A43.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A44.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A45.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A46.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A47.jpg",
    "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A48.jpg",
]

# 用户管理
class User(AbstractBaseUser):
    user_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    # last_login = models.DateTimeField(default=datetime.datetime.now)

    USERNAME_FIELD = "name"
    
    avatar = models.CharField(max_length=MAX_CHAR_LENGTH, default="")
    
    def save(self, *args, **kwargs):
        if not self.avatar:
            default_avatars = [
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A41.jpg",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A42.jpg",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A43.jpg",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A44.jpg",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A45.jpg",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A46.png",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A47.png",
                "https://killthisse-avatar.oss-cn-beijing.aliyuncs.com/%E9%BB%98%E8%AE%A48.png",
            ]
            self.avatar = random.choice(default_avatars)
        super().save(*args, **kwargs)
    
    # 邮箱 
    user_email = models.CharField(max_length=MAX_CHAR_LENGTH, default="2365269662@qq.com")
    # 手机号
    user_phone = models.IntegerField(default=0)
    # 验证码 每次登录都会销毁、更新
    user_code = models.IntegerField(default=0)
    # 验证码创建的时间戳
    user_code_created_time = models.FloatField(default=0)
    # 是否注销
    disabled = models.BooleanField(default=False)
    
    def serialize(self):
        return {
            "user_id": self.user_id, 
            "name": self.name, 
            "avatar": self.avatar,
            "user_email": self.user_email,
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

# 好友请求
class FriendshipRequest(models.Model):
    user_id = models.IntegerField()
    friend_user_id = models.IntegerField()
    update_time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = ('user_id', 'friend_user_id')
        
        
# 群组
class Group(models.Model):
    group_id = models.BigAutoField(primary_key=True)
    group_name = models.CharField(max_length=MAX_NAME_LENGTH) # group name
    admin_id = models.IntegerField()  # group admin
    update_time = models.DateTimeField(default=datetime.datetime.now)  # update time

    def serialize(self):
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "admin_id": self.admin_id,
            "update_time": self.update_time
        }
    
    class Meta:
        unique_together = ('group_id', 'group_name')
    
# 群组成员和分组id的绑定关系
class GroupFriend(models.Model):
    group_id = models.IntegerField() # group id
    user_id = models.IntegerField()  # user id
    update_time = models.DateTimeField(default=datetime.datetime.now)  # update time
    
    class Meta:
        unique_together = ('group_id', 'user_id')
    
# 群聊邀请
class GroupInvitation(models.Model):
    # 主键：id
    invitation_id = models.BigAutoField(primary_key=True)
    # 邀请者id
    inviter_id = models.IntegerField()
    # 被邀请者id
    invitee_id = models.IntegerField()
    # 群聊id
    group_id = models.IntegerField()
    # 更新时间
    update_time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = ('invitee_id', 'group_id')

