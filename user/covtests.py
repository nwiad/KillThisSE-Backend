import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.hashers import make_password
from user.models import User, FriendshipRequest, Group, GroupFriend, Friendship,GroupInvitation
from msg.models import Conversation, Message
from user.views import UserViewSet
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
from django.urls import reverse
from unittest.mock import patch
import time

SENDFR = "/user/send_friend_request/"
RESETNAME = "/user/reset_name/"
RESETPW = "/user/reset_password/"

# 成功注册 without email
def register_someone(self, data):
    response = self.client.post("/user/register_without_email/", data=data, content_type="application/json")
    response_content = json.loads(response.content)
    expected_content = {"code": 0, "info": "Succeed", "Created": True}
    self.assertEqual(response_content, expected_content)
    return response

# 尝试注册
def register_try(self, data):
    response = self.client.post("/user/register_without_email/", data=data, content_type="application/json")
    return response

# 成功登录
def login_someone(self, data):
    response = self.client.post("/user/login/", data=data, content_type="application/json")
    response_content = json.loads(response.content)
    self.assertEqual(response.status_code, 200)
    self.assertIn("Token", response_content) 
    return response

# 尝试登录
def login_try(self, data):
    response = self.client.post("/user/login/", data=data, content_type="application/json")
    return response
