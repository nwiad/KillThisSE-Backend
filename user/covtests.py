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


# class ConversationTestCasenaive(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user1 = User.objects.create(name='user1', password=make_password('password'))
#         self.user2 = User.objects.create(name='user2', password=make_password('password'))
#         self.user3 = User.objects.create(name='user3', password=make_password('password'))
#         self.user4 = User.objects.create(name='user4', password=make_password('password'))
#         addFriends(self.user1, self.user2)
#         addFriends(self.user1, self.user3)
#         self.conversation = Conversation.objects.create(is_Private=True)
#         self.conversation.members.add(self.user1, self.user2)

#     # 获取所有的私聊会话
#     def test_get_private_conversations(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "token": token
#         }
        
#         url = '/user/get_private_conversations/'
#         self.client.post(url, data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json(), {
#             'code': 0, 
#             'info': 'Succeed', 
#             'Logged in': True,
#             'Token': token
#         })

#     # 获取或创建私聊会话
#     def test_get_or_create_private_conversation(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]

#         data = {
#             "token": token,
#             'friend': self.user2.user_id
#         }
#         url = '/user/get_or_create_private_conversation/'
#         # Test successful get
#         response = self.client.post(url, data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json(), {
#             'code': 0, 
#             'info': 'Succeed',
#             "conversation_id": self.conversation.conversation_id,
#             "silent": False
#         })
        
#         # Test successful create
#         response = self.client.post(url, {'friend': self.user3.user_id, "token": token},content_type="application/json")

#         self.assertEqual(response.status_code, 200)
#         conversation = Conversation.objects.filter(members__in=[self.user1], is_Private=True).filter(members__in=[self.user3]).first()
#         self.assertTrue(conversation is not None)
#         self.assertEqual(response.json(), {
#             'code': 0, 
#             'info': 'Succeed',
#             "conversation_id": conversation.conversation_id,
#             "silent": False
#         })
#         # Test friend does not exist
#         response = self.client.post(url, {'friend': 999, "token": token},content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json(), {
#             'code': 2, 'info': 'Friend does not exist'
#         })
#         # Test you are not friends
#         response = self.client.post(url, {'friend': self.user4.user_id, "token": token},content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json(), {
#             'code': 3, 'info': 'You are not friends'
#         })
      
#     # 获取所有的群聊会话
#     def test_get_group_conversations(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "token": token
#         }
        
#         url = '/user/get_group_conversations/'
#         self.client.post(url, data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json(), {
#             'code': 0, 
#             'info': 'Succeed', 
#             'Logged in': True,
#             'Token': token
#         })
        
#     # 获取或创建群聊会话
    
# class CreateGroupConversationTestCase(TestCase):
#     def setUp(self):
#         self.user1 = User.objects.create(name="user1", password=make_password("password"))
#         self.user2 = User.objects.create(name="user2", password=make_password("password"))
#         self.user3 = User.objects.create(name="user3", password=make_password("password"))
#         addFriends(self.user1, self.user2)
        
#     def test_create_group_conversation(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "token": token
#         }
        
#         url = '/user/get_group_conversations/'
#         self.client.post(url, data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
        
#         data = {
#             "members": [self.user2.user_id],
#             "name": "Group Conversation",
#             "token": token
            
#         }
#         response = self.client.post("/user/create_group_conversation/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json()["code"], 0)
#         self.assertIsNotNone(response.json()["conversation_id"])

#         conversation_id = response.json()["conversation_id"]
#         conversation = Conversation.objects.get(conversation_id=conversation_id)
#         self.assertEqual(conversation.conversation_name, "Group Conversation")
#         self.assertFalse(conversation.is_Private)
#         self.assertEqual(conversation.owner, self.user1.user_id)
#         self.assertIn(self.user1, conversation.members.all())
#         self.assertIn(self.user2, conversation.members.all())

#         #  test_create_group_conversation_member_not_exist(self):
#         data = {
#             "members": [self.user2.user_id, 999],
#             "name": "Group Conversation",
#             "token": token
#         }
#         response = self.client.post("/user/create_group_conversation/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 2)
#         self.assertEqual(response.json()["info"], "member not exist")
#         self.client.force_login(self.user1)

#     def test_create_group_conversation_not_friend(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "token": token
#         }
        
#         data = {
#             "members": [self.user3.user_id],
#             "name": "Group Conversation",
#             "token": token
#         }
#         response = self.client.post("/user/create_group_conversation/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 3)
#         self.assertEqual(response.json()["info"], "user3 is not your friend")

# class GroupInvitationTestCasebyAdmin(TestCase):
#     def setUp(self):
#         self.user1 = User.objects.create(name="user1", password=make_password("password"))
#         self.user2 = User.objects.create(name="user2", password=make_password("password"))
#         self.user3 = User.objects.create(name="user3", password=make_password("password"))
#         self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
#         self.group_conversation.members.add(self.user1, self.user2)
#         self.group_conversation.administrators.add(self.user1)

#     def test_admin_invite_member(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [self.user3.user_id],
#             "token": token
#         }
#         response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json()["Invited"], True)

#         self.assertTrue(self.user3 in self.group_conversation.members.all())

#     def test_admin_invite_member_group_not_exist(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": 999,
#             "invitee": [self.user3.user_id],
#             "token": token
#         }
#         response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 2)
#         self.assertEqual(response.json()["info"], "Group does not exist")

#     def test_admin_invite_member_permission_denied(self):
#         data = {
#             "name": "user2",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [self.user3.user_id],
#             "token": token
#         }
#         response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 5)
#         self.assertEqual(response.json()["info"], "Permission denied")

#     def test_admin_invite_member_invitee_not_exist(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [999],
#             "token": token
#         }
#         response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 3)
#         self.assertEqual(response.json()["info"], "The user you tried to invite does not exist")

#     def test_admin_invite_member_user_already_in_group(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [self.user2.user_id],
#             "token": token
#         }
#         response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 4)
#         self.assertEqual(response.json()["info"], "User is already in the group")

# class InviteMemberToGroupTestCase(TestCase):
#     def setUp(self):
#         self.user1 = User.objects.create(name="user1", password=make_password("password"))
#         self.user2 = User.objects.create(name="user2", password=make_password("password"))
#         self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
#         self.group_conversation.members.add(self.user1)

#     def test_invite_member_to_group(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [self.user2.user_id],
#             "token": token
#         }
#         response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json()["Invited"], True)

#     def test_invite_member_to_group_group_not_exist(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": 999,
#             "invitee": [self.user2.user_id],
#             "token":token
#         }
#         response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 2)
#         self.assertEqual(response.json()["info"], "Group does not exist")

#     def test_invite_member_to_group_invitee_not_exist(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [999],
#             "token": token
#         }
#         response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 3)
#         self.assertEqual(response.json()["info"], "The user you tried to invite does not exist")

#     def test_invite_member_to_group_user_already_in_group(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "invitee": [self.user1.user_id],
#             "token": token
#         }
#         response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 4)
#         self.assertEqual(response.json()["info"], "User is already in the group")

# class GetGroupInvitationsTestCase(TestCase):
#     def setUp(self):
#         self.user1 = User.objects.create(name="user1", password=make_password("password"))
#         self.user2 = User.objects.create(name="user2", password=make_password("password"))
#         self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
#         self.group_conversation.members.add(self.user1)
#         self.group_invitation = GroupInvitation.objects.create(inviter_id=self.user2.user_id, invitee_id=self.user1.user_id, group_id=self.group_conversation.conversation_id)

#     def test_get_group_invitations(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": self.group_conversation.conversation_id,
#             "token": token
#         }
#         response = self.client.post("/user/get_group_invitations/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         return_data = response.json()
#         invitations = return_data["invitations"]
#         self.assertEqual(len(invitations), 1)

#         invitation = invitations[0]
#         self.assertEqual(invitation["invitation_id"], self.group_invitation.invitation_id)
#         self.assertEqual(invitation["inviter_id"], self.user2.user_id)
#         self.assertEqual(invitation["inviter_name"], self.user2.name)
#         self.assertEqual(invitation["inviter_avatar"], self.user2.avatar)
#         self.assertEqual(invitation["invitee_id"], self.user1.user_id)
#         self.assertEqual(invitation["invitee_name"], self.user1.name)
#         self.assertEqual(invitation["invitee_avatar"], self.user1.avatar)

#     def test_get_group_invitations_group_not_exist(self):
#         data = {
#             "name": "user1",
#             "password": "password"
#         }
#         response = login_someone(self, data)
#         token = response.json()["Token"]
#         data = {
#             "group": 999,
#             "token": token
#         }
#         response = self.client.post("/user/get_group_invitations/", data=data, content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json()["code"], 2)
#         self.assertEqual(response.json()["info"], "Group does not exist")

class RespondGroupInvitationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
        self.group_conversation.members.add(self.user2)
        self.group_invitation = GroupInvitation.objects.create(inviter_id=self.user2.user_id, invitee_id=self.user1.user_id, group_id=self.group_conversation.conversation_id)

    def test_respond_group_invitation_group_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": 999,
            "invitation": self.group_invitation.invitation_id,
            "response": "accept",
            "token": token
        }
        response = self.client.post("/user/respond_group_invitation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "group does not exist")

    def test_respond_group_invitation_permission_denied(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitation": self.group_invitation.invitation_id,
            "response": "accept",
            "token": token
        }
        response = self.client.post("/user/respond_group_invitation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 3)
        self.assertEqual(response.json()["info"], "Permission denied")


class GroupConversationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False, owner=self.user1.user_id)
        self.group_conversation.members.add(self.user1, self.user2)
        self.group_conversation.administrators.add(self.user1)

    def test_dismiss_group_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "token": token
        }
        response = self.client.post("/user/dismiss_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Dismissed"], True)

        dismissed_conversation = Conversation.objects.filter(conversation_id=self.group_conversation.conversation_id).first()
        self.assertTrue(dismissed_conversation.disabled)

    def test_dismiss_group_conversation_group_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": 999,
            "token": token
        }
        response = self.client.post("/user/dismiss_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "Group not exist")

    def test_dismiss_group_conversation_not_owner(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "token": token
        }
        response = self.client.post("/user/dismiss_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 3)
        self.assertEqual(response.json()["info"], "You are not the owner of this group")

    def test_leave_group_conversation(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "token": token
        }
        response = self.client.post("/user/leave_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Left"], True)

        left_conversation = Conversation.objects.filter(conversation_id=self.group_conversation.conversation_id).first()
        self.assertTrue(self.user2 not in left_conversation.members.all())

    def test_leave_group_conversation_group_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": 999,
            "token": token
        }
        response = self.client.post("/user/leave_group_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "Group not exist")
