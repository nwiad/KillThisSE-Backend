import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.hashers import make_password
from user.models import User, FriendshipRequest, Group, GroupFriend, Friendship
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


class ConversationTestCasenaive(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create(name='user1', password=make_password('password'))
        self.user2 = User.objects.create(name='user2', password=make_password('password'))
        self.user3 = User.objects.create(name='user3', password=make_password('password'))
        self.user4 = User.objects.create(name='user4', password=make_password('password'))
        addFriends(self.user1, self.user2)
        addFriends(self.user1, self.user3)
        self.conversation = Conversation.objects.create(is_Private=True)
        self.conversation.members.add(self.user1, self.user2)

    # 获取所有的私聊会话
    def test_get_private_conversations(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        
        url = '/user/get_private_conversations/'
        self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'code': 0, 
            'info': 'Succeed', 
            'Logged in': True,
            'Token': token
        })

    # 获取或创建私聊会话
    def test_get_or_create_private_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        data = {
            "token": token,
            'friend': self.user2.user_id
        }
        url = '/user/get_or_create_private_conversation/'
        # Test successful get
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'code': 0, 
            'info': 'Succeed',
            "conversation_id": self.conversation.conversation_id,
            "silent": False
        })
        
        # Test successful create
        response = self.client.post(url, {'friend': self.user3.user_id, "token": token},content_type="application/json")

        self.assertEqual(response.status_code, 200)
        conversation = Conversation.objects.filter(members__in=[self.user1], is_Private=True).filter(members__in=[self.user3]).first()
        self.assertTrue(conversation is not None)
        self.assertEqual(response.json(), {
            'code': 0, 
            'info': 'Succeed',
            "conversation_id": conversation.conversation_id,
            "silent": False
        })
        # Test friend does not exist
        response = self.client.post(url, {'friend': 999, "token": token},content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'code': 2, 'info': 'Friend does not exist'
        })
        # Test you are not friends
        response = self.client.post(url, {'friend': self.user4.user_id, "token": token},content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'code': 3, 'info': 'You are not friends'
        })
      
    # 获取所有的群聊会话
    def test_get_group_conversations(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        
        url = '/user/get_group_conversations/'
        self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'code': 0, 
            'info': 'Succeed', 
            'Logged in': True,
            'Token': token
        })
        
    # 获取或创建群聊会话
    
class CreateGroupConversationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.user3 = User.objects.create(name="user3", password=make_password("password"))
        addFriends(self.user1, self.user2)
        
    def test_create_group_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        
        url = '/user/get_group_conversations/'
        self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        data = {
            "members": [self.user2.user_id],
            "name": "Group Conversation",
            "token": token
            
        }
        response = self.client.post("/user/create_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], 0)
        self.assertIsNotNone(response.json()["conversation_id"])

        conversation_id = response.json()["conversation_id"]
        conversation = Conversation.objects.get(conversation_id=conversation_id)
        self.assertEqual(conversation.conversation_name, "Group Conversation")
        self.assertFalse(conversation.is_Private)
        self.assertEqual(conversation.owner, self.user1.user_id)
        self.assertIn(self.user1, conversation.members.all())
        self.assertIn(self.user2, conversation.members.all())

        #  test_create_group_conversation_member_not_exist(self):
        data = {
            "members": [self.user2.user_id, 999],
            "name": "Group Conversation",
            "token": token
        }
        response = self.client.post("/user/create_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "member not exist")
        self.client.force_login(self.user1)

    def test_create_group_conversation_not_friend(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        
        data = {
            "members": [self.user3.user_id],
            "name": "Group Conversation",
            "token": token
        }
        response = self.client.post("/user/create_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 3)
        self.assertEqual(response.json()["info"], "user3 is not your friend")
