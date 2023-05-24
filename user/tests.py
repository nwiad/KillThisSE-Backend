import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.hashers import make_password
from user.models import User, FriendshipRequest, Group, GroupFriend, Friendship, GroupInvitation
from msg.models import Conversation, Message
from user.views import UserViewSet
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
from django.urls import reverse
from unittest.mock import patch
import time

SENDFR = "/user/send_friend_request/"
RESETNAME = "/user/reset_name/"
RESETPW = "/user/reset_password/"

# region test utils
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

# by name
def sbn(self, data):
    response = self.client.post("/user/search_by_name/", data=data, content_type="application/json")
    return response

# by id
def sbi(self, data):
    response = self.client.post("/user/search_by_id/", data=data, content_type="application/json")
    return response

# by fname 
def sfbn(self, data):
    response = self.client.post("/user/search_friend_by_name/", data=data, content_type="application/json")
    return response

# by fid
def sfbi(self, data):
    response = self.client.post("/user/search_friend_by_id/", data=data, content_type="application/json")
    return response

# del friend
def delf(self, data):
    response = self.client.post("/user/del_friend/", data=data, content_type="application/json")
    return response

# endregion


class UserViewTests(TestCase):
    # create a user object that is common across all test methods
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            name = "testuser", 
            password = make_password("12345678"),
            user_email = "2365269662@qq.com"
            )
        user00 = User.objects.create(
            name="user000", 
            password=make_password("password000"),
            user_email = "2365269662@qq.com"
            )
        addFriends(cls.user, user00)
        
        
    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserViewSet()
        self.client = Client()
      
        
# region 无邮箱验证注册
    # 正常注册
    def test_successful_user_registration(self):
        request_data = {
            "name": "testuser0",
            "password": "newpassword0"
        }
        response = register_someone(self, request_data)
        self.assertTrue(User.objects.filter(name="testuser0").exists())

    # 非法用户名
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser12345678901234567890",
            "password": "testpassword"
        }
        response = register_try(self, request_data)
        self.assertEqual(response.status_code, 400)
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 1, "info": "用户名不合法"})

    # 重复注册
    def test_duplicate_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword"
        }
        response = register_try(self, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(name="testuser", password=make_password("testpassword")).exists())
        self.assertEqual(json.loads(response.content), {"code": 2, "info": "用户名已经存在"})
        
    # 非法密码
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser123",
            "password": "tes"
        }
        response = register_try(self, request_data)
        self.assertEqual(response.status_code, 400)
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 3, "info": "密码不合法"})
# endregion


# region 注销账户
    # 注销账户
    def test_cancel_account(self):
        request_data = {
            "name": "testuser1",
            "password": "newpassword1"
        }
        response = register_try(self, request_data)
        self.assertEqual(response.status_code, 200)
        # log in user
        response = login_someone(self, request_data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        response = self.client.post("/user/cancel_account/", data=data, content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"code": 0, "info": "Succeed", "Deleted": true}')
# endregion


# region login ok
    # 正常登录
    def test_successful_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "12345678"
            }
        
        response = login_someone(self, request_data)
        self.assertTrue("Token" in response.json())
        
        # 重复登录
        rep_data = {
            "name": "testuser",
            "password": "12345678"
            }
        response = login_try(self, rep_data)
        self.assertTrue("Token" in response.json())
    
    # 用户名不合法
    def test_wrong_password_user_login(self):
        il_data = {
            "name": "te",
            "password": "testpassword"
        }
        response = login_try(self, il_data)
        self.assertEqual(json.loads(response.content), {"code": 1, "info": "用户名不合法"})
    
    # 试图登录不存在的用户
    def test_nonexsit_user_login(self):
        non_data = {
            "name": "nonexsitentuser",
            "password": "testpassword"
        }
            
        response = login_try(self, non_data)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, {"code": 2, "info": "用户不存在"})
    
    # 错误密码
    def test_wrong_password_user_login(self):
        wp_data = {
            "name": "testuser",
            "password": "wrongpassword"
        }
        response = login_try(self, wp_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {"code": 3, "info": "用户名或密码错误"})
       
    # logout
    def test_successful_logout(self):
        # log in
        data = {
            "name": "testuser",
            "password": "12345678"
        }
        response = login_someone(self, data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["Token"]
        
        data = {"token": token}
        # Log out
        response = self.client.post(reverse("user-logout"), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Logged out": True})
       
# endregion


# region login by email ok
    #todo 正常登录
    def test_successful_user_login_with_email(self):
        user = User.objects.create(name="test_user", 
                                   password=make_password("password")
                                   )
        user.user_email = "test@example.com"
        user.user_code = 123456  # Assuming you have a function to generate a verification code
        user.user_code_created_time = time.time()
        user.save()

        data = {
            "email": "test@example.com",
            "code_input": user.user_code
        }
        response = self.client.post("/user/login_with_email/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["Logged in"])
        self.assertIsNotNone(response.json()["Token"])
        token = response.json()["Token"]
        data = {"token": token}
        
        # log out
        response = self.client.post(reverse("user-logout"), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Logged out": True})
       
        # 错误验证码登录
        data = {
            "email": "test@example.com",
            "code_input": user.user_code +1
        }
        response = self.client.post("/user/login_with_email/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),{'code': 5, 'info': '验证码错误'})


    def test_not_exist_user_login_with_email(self):
        data = {
            "email": "DoesNotExist@Nope.com",
            "code_input": 123456
        }
        response = self.client.post("/user/login_with_email/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(),{'code': 2, 'info': '用户不存在'})

# endregion


# region modify ok
    def test_reset_name(self):
        # log in
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        user = User.objects.get(name="testuser")
        data = {
            "name": "newtestuser",
            "token": token
        }

        # 修改用户名成功
        response = self.client.post(
            RESETNAME,
            data=data,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Modified": True})

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.name, "newtestuser")


        # 2 illegal username
        response = self.client.post(
            RESETNAME,
            {
                "name": "illegal!name",
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"code": 1, "info": "Not logged in"})

        # 3 username already exists
        response = self.client.post(
            RESETNAME,
            {
                "name": "newtestuser",
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"code": 1, "info": "Not logged in"})
    
    def test_reset_email(self):
        # log in
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["Token"]
        
        response = self.client.post(
            "/user/reset_email/",
            {
                "password":"12345678",
                "email":"email@163.com",
                "token": token
            },
            content_type="application/json"
        )
        user = User.objects.get(name="testuser")
        
        self.assertEqual(response.json(), {'Reset': True, 'code': 0, 'info': 'Succeed'})
        self.assertEqual(response.status_code, 200)
        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.user_email, "email@163.com")
    
    def test_reset_password(self):
        # log in
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["Token"]
        
        # 修改密码
        response = self.client.post(
            "/user/reset_password/",
            {
                "old_pwd": "12345678",
                "new_pwd": "23232323",
                "token": token
            },
            content_type="application/json"
        )
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Modified": True})
        self.assertEqual(response.status_code, 200)
        # 登出用户
        data = {
            "token" : token
        }
        # Log out
        response = self.client.post(reverse("user-logout"), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Logged out": True})

        # 用新密码登录
        login_data = {
            "name": "testuser", 
            "password": "23232323"
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
  
    def test_reset_password_old_wrong(self):
        # log in
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["Token"]
        
        # 修改密码
        response = self.client.post(
            "/user/reset_password/",
            {
                "old_pwd": "123456",
                "new_pwd": "23232323",
                "token": token
            },
            content_type="application/json"
        )
        self.assertEqual(response.json(), {'code': 2, 'info': '旧密码错误'})
             
    def test_reset_avatar(self):
        # log in
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["Token"]
        
        user = User.objects.get(name="testuser")

        # 修改头像
        response = self.client.post(
            "/user/reset_avatar/",
            {
                "avatar": "newavatar",
                "token": token
            },
            content_type="application/json"
        )
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Modified": True})
        self.assertEqual(response.status_code, 200)

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.avatar, "newavatar")
# endregion  
 
     
# region friend add ok
    # send_friend_request
    def test_send_friend_request(self):
        # 创建两个新用户并登录1
        user1 = User.objects.create(name="testuser1", password=make_password("newpassword1"))
        user2 = User.objects.create(name="testuser2", password=make_password("newpassword2"))
        # 登录1
        login_data = {"name": "testuser1", "password": "newpassword1"}
        
        response = login_someone(self, login_data)
        token = response.json()["Token"]

        # 发送好友请求
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": user2.user_id,
                "token": token
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        
        # 检查好友请求是否已发送
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)
        
        # 发送好友请求失败： 好友不存在
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": 999,
                "token": token
            },
            content_type="application/json"
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 2, "info": "搜索目标不存在"})
        
        
        # 发送好友请求失败： 重复发送
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": user2.user_id,
                "token": token
            },
            content_type="application/json"
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 4, 'info': '请求已经存在，请耐心等待'})


        # 登出
        data = {
            "token" : token
        }
        response = self.client.post(reverse("user-logout"), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Logged out": True})

        self.client.cookies["session"] = "session_value5"

        # 登录2
        login_data = {"name": "testuser2", "password": "newpassword2"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        # 2又向1 发送好友请求
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": user1.user_id,
                "token": token
            },
            content_type="application/json"
        )
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 0, "info": "Succeed", "Become Friends successfully": True})
                
        # 清除session 登录另一个用户需要换session！
        self.client.cookies["session"] = "session_value4"
        

        # testuser 和 user000 已经是好友
        # 登录1
        login_data = {"name": "testuser", "password": "12345678"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        user3 = User.objects.get(name="user000")
        
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": user3.user_id,
                "token": token
            },
            content_type="application/json"
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 3, "info": "你们已经是好友啦！"})
        
    # get_friend_requests
    def test_get_friend_requests(self):
        # create users
        user1 = User.objects.create(name="user1", password=make_password("password1"))
        user2 = User.objects.create(name="user2", password=make_password("password2"))
        user3 = User.objects.create(name="user3", password=make_password("password3"))

        # create friendship requests 2 3给1发请求
        sendFriendRequest(user1=user2, user2=user1)
        sendFriendRequest(user1=user3, user2=user1)
        
        # log in as user1
        login_data = {
            "name": "user1", 
            "password": "password1"
            }
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        data = {
            "token" : token
        }
        # test case: successfully get friend requests
        response = self.client.post("/user/get_friend_requests/", data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.json(), {
            "code": 0, 
            "info": "Succeed",
            "requests": [
                {
                    "user_id": user2.user_id,
                    "name": user2.name,
                    "avatar": user2.avatar
                },
                {
                    "user_id": user3.user_id,
                    "name": user3.name,
                    "avatar": user3.avatar
                }
            ]
        })

        # test case: no friend requests
        
        FriendshipRequest.objects.all().delete()
        response = self.client.post("/user/get_friend_requests/", data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "requests": []})

    # respond_friend_request  ok
    def test_respond_friend_request(self):
        # 创建两个新用户       
        user1 = User.objects.create(name="testuser11", password=make_password("newpassword11"))
        user2 = User.objects.create(name="testuser22", password=make_password("newpassword22"))

        # 登录第一个用户
        login_data = {"name": "testuser11", "password": "newpassword11"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]

        # 发送好友请求
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": user2.user_id,
                "token": token
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        # 检查好友请求是否已发送  参数1 向参数2发送的请求存在
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)

        # 登出
        data = {
            "token" : token
        }
        response = self.client.post(reverse("user-logout"), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Logged out": True})

        # 清除session 登录另一个用户需要换session！
        self.client.cookies["session"] = "session_value2"
        
        # 登录第二个用户
        login_data = {"name": "testuser22", "password": "newpassword22"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        # 接受好友请求
        response = self.client.post(
            "/user/respond_friend_request/",
            {
                "friend_user_id": user1.user_id, 
                "response": "accept",
                "token": token
                },
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Become Friends": True})

        # 检查用户是否已成为好友
        are_friends = isFriend(user1, user2)
        self.assertTrue(are_friends)
    
    # respond_friend_request  no
    def test_respond_friend_request(self):
        # 创建两个新用户
        user1 = User.objects.create(name="testuser11", password=make_password("newpassword11"))
        user2 = User.objects.create(name="testuser22", password=make_password("newpassword22"))
        
        # 登录第一个用户
        login_data = {"name": "testuser11", "password": "newpassword11"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        # 发送好友请求
        response = self.client.post(
            SENDFR, 
            {
                "friend_user_id": user2.user_id,
                "token": token    
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        # 检查好友请求是否已发送  参数1 向参数2发送的请求存在
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)

        # 登出
        data = {
            "token" : token
        }
        response = self.client.post(reverse("user-logout"), json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Logged out": True})

        # 清除session 登录另一个用户需要换session！
        self.client.cookies["session"] = "session_value2"
        
        # 登录第二个用户
        login_data = {"name": "testuser22", "password": "newpassword22"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        # 接受好友请求
        response = self.client.post(
            "/user/respond_friend_request/",
            {
                "friend_user_id": user1.user_id, 
                "response": "reject",
                "token": token
                },
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Become Friends": False})

        # 检查用户是否已成为好友
        are_friends = isFriend(user1, user2)
        self.assertFalse(are_friends)
    
# endregion
  
  
# region friend del ok
    def test_del_friend(self):
        # 创建测试用户和好友
        user = User.objects.create(name="test_user", password=make_password("password"))
        friend = User.objects.create(name="test_friend", password=make_password("password"))
        
        # 创建好友关系
        addFriends(user, friend)
        
        # 登录user 
        login_data = {"name": "test_user", "password": "password"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        # 模拟请求
        data={
            "friend_user_id": friend.user_id,
            "token":token
        }
        response = delf(self, data)
  
        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"code": 0, "info": "Succeed", "Deleted": True})
        
        # 确认好友关系已删除
        are_friends = isFriend(user, friend)
        self.assertFalse(are_friends)
        
        # 删除不存在的好友
        data={
            "friend_user_id": 999,
            "token":token
        }
        response = delf(self, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 2, "info": "用户不存在"})
        
        # 删除非好友
        data={
            "friend_user_id": user.user_id,
            "token":token
        }
        response = delf(self, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 3, "info": "Ta不是你的朋友T_T"})
        
        user.delete()
        friend.delete()

# endregion


# region get profile ok
    def test_get_profile(self):
        # 创建测试用户
        user = User.objects.create(
            name="test_user", 
            password=make_password("password")
            )
        # 登录user 
        login_data = {"name": "test_user", "password": "password"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        data = {
            "token" : token
        }
        # 模拟请求
        response = self.client.post("/user/get_profile/", data = data, content_type="application/json")
  
        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)        
        # 删除测试用户
        user.delete()
        
    def test_get_avatar(self):
        user = User.objects.create(
            name="test_user", 
            password=make_password("password")
            )
        # 登录user 
        login_data = {"name": "test_user", "password": "password"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        data = {
            "token" : token
        }
        response = self.client.post("/user/get_profile/", data = data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["avatar"], user.avatar)

    def test_get_avatar(self):
        user = User.objects.create(
            name="test_user", 
            password=make_password("password")
            )
        # 登录user 
        login_data = {"name": "test_user", "password": "password"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        data = {
            "token" : token,
            "name": "Whatever"
        }
        response = self.client.post("/user/get_avatar/", data = data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 2, "info": "目标用户不存在"})
# endregion


# region search user ok 
    # by id
    def test_search_by_id(self):
        # 创建测试用户
        user = User.objects.create(name="test_user", password=make_password("password"))
        
        # 登录user 
        login_data = {"name": "test_user", "password": "password"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        teuser = User.objects.get(name="testuser")
        # 模拟请求 成功
        data={
            "friend_user_id": teuser.user_id,
            "token" : token
        }
        response = sbi(self, data)
        

        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 
            {"code": 0, 
             "info": "Succeed", 
             "user_id": teuser.user_id, 
             "name": teuser.name,
             "avatar": teuser.avatar
            })
        
        # 搜索无效id
        data={
            "friend_user_id": 999,
            "token" : token
        }
        response = sbi(self, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code":2, "info": "查找用户不存在"})
        # 删除测试用户
        user.delete()

    # by name
    def test_search_by_id(self):
        # 创建测试用户
        user = User.objects.create(name="test_user", password=make_password("password"))
        
        # 登录user 
        login_data = {"name": "test_user", "password": "password"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        teuser = User.objects.get(name="testuser")
        # 模拟请求 成功
        data={
            "friend_name": teuser.name,
            "token": token
        }
        response = sbn(self, data)

        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 
            {"code": 0, 
             "info": "Succeed", 
             "user_id": teuser.user_id, 
             "name": teuser.name,
             "avatar": teuser.avatar
            })
        
        # 搜索无效id
        data={
            "friend_name": "99999",
            "token": token
        }
        
        response = sbn(self, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code":2, "info": "查找用户不存在"})
        # 删除测试用户
        user.delete()
# endregion


# region search user in friend list ok
    # by id
    def test_search_friend_by_id(self):
        # 登录user 
        login_data = {"name": "testuser", "password": "12345678"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        user01 = User.objects.get(name="testuser")
        user00 = User.objects.get(name="user000")
        # 失败
        data={
            "friend_id": 999,
            "token": token
        }
        response = sfbi(self, data)

        self.assertEqual(response.json(),{"code": 2, "info": "查找用户不存在"})
        
        # 成功
        aref = isFriend(user01, user00)
        self.assertTrue(aref)
        
        data={
            "friend_id": user00.user_id,
            "token": token
        }
        response = sfbi(self, data)
        self.assertEqual(response.json(),
                         {
                            "code": 0, 
                            "info": "Succeed", 
                            "user_id":user00.user_id, 
                            "avatar": user00.avatar,
                            "name": user00.name
                         })

    # by name
    def test_search_friend_by_name(self):
        # 登录user 
        login_data = {"name": "testuser", "password": "12345678"}
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        user01 = User.objects.get(name="testuser")
        user00 = User.objects.get(name="user000")
        # 失败 不存在此人
        data={
            "friend_name": "99999",
            "token": token
        }
        response = sfbn(self, data)

        self.assertEqual(response.json(),{"code": 2, "info": "查找用户不存在"})
        
        
        userstanger = User.objects.create(name="stranger", password=make_password("password"))
        
        # 失败 非好友    
        data={
            "friend_name": userstanger.name,
            "token": token
        }
        response = sfbn(self, data)
        
        self.assertEqual(response.json(),{"code": 2, "info": "查找用户不存在"})
        
        # 成功
        aref = isFriend(user01, user00)
        self.assertTrue(aref)
        
        data={
            "friend_name": user00.name,
            "token": token
        }
        response = sfbn(self, data)
        
        self.assertEqual(response.json(),
                        {
                        "code": 0, 
                        "info": "Succeed", 
                        "user_id":user00.user_id, 
                        "avatar": user00.avatar,
                        "name": user00.name
                        })
# endregion


# region ok  好友列表
    def test_get_friends(self):
        data = {
            "name": "testuser", 
            "password": "12345678"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        response = self.client.post("/user/get_friends/", data = data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        list = []
        for who in User.objects.all():
            if isFriend(User.objects.get(name="testuser"), who):
                list.append({
                    "avatar":who.avatar,
                    "name":who.name,
                    "user_id":who.user_id
                    })
        
        self.assertEqual(response.json(), {"code": 0, "friends": list, "info": "Succeed"})
        
# endregion        
   
        
# region ok 好友分组
    # 创建和删除分组
    def test_create_group(self):
        User.objects.create(name="testuser111", password=make_password("12345678"))
        data = {
            "name": "testuser111", 
            "password": "12345678"
            }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token, 
            "name": "test_group"
            }
        
        # 创建分组
        response = self.client.post("/user/create_group/", data = data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        group = Group.objects.get(group_name="test_group")
        self.assertEqual(response.json(), {"code": 0, "group_id": group.group_id, "info": "Succeed"})
        
        # 删除分组
        response = self.client.post("/user/del_group/", data = data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        group = Group.objects.filter(group_name="test_group")
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Deleted': True})
        self.assertFalse(group)

    # 获取分组
    def test_get_group(self):
        User.objects.create(name="testuser111", password=make_password("12345678"))
        data = {
            "name": "testuser111",
            "password": "12345678"
            }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        # 获取分组
        response = self.client.post("/user/get_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        expected_data = {
            'code': 0, 
            'info': 'Succeed', 
            'groups': []
        }
        self.assertEqual(response.json(), expected_data)

    # 获取分组成员
    def test_get_group_friends(self):
        user = User.objects.create(name="testuser111", password=make_password("12345678"))
        data = {
            "name": "testuser111",
            "password": "12345678"
            }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        group = Group.objects.create(group_name="test_group", admin_id=user.user_id)
        friend = User.objects.create(name="friend", password=make_password("12345678"))
        group_friend = GroupFriend.objects.create(group_id=group.group_id, user_id=friend.user_id)


        data = {
            "group_id": group.group_id,
            "token": token
        }
        response = self.client.post("/user/get_group_friends/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)

        expected_data = {
            'code': 0, 
            'info': 'Succeed', 
            "friends": [
                {
                    "user_id": friend.user_id,
                    "name": friend.name,
                    "avatar": friend.avatar
                }
            ]
        }
        self.assertEqual(response.json(), expected_data)
    
    # 往分组里添加/删除好友
    def test_add_friend_to_group(self):
        user = User.objects.create(name="testuser111", password=make_password("12345678"))
        data = {
            "name": "testuser111",
            "password": "12345678"
            }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        group = Group.objects.create(group_name="test_group", admin_id=user.user_id)
        friend = User.objects.create(name="friend", password=make_password("12345678"))
        friendship = Friendship.objects.create(user_id=user.user_id, friend_user_id=friend.user_id)

        data = {
            "group_id": group.group_id,
            "friend_id": friend.user_id,
            "token": token
        }
        response = self.client.post("/user/add_friend_to_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Added': True})

        group_friend = GroupFriend.objects.filter(group_id=group.group_id, user_id=friend.user_id).first()
        self.assertIsNotNone(group_friend)
        
        # 删除好友
        data = {
            "group_id": group.group_id,
            "friend_id": friend.user_id,
            "token": token
        }
        response = self.client.post("/user/del_friend_from_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Deleted': True})

        group_friend = GroupFriend.objects.filter(group_id=group.group_id, user_id=friend.user_id).first()
        self.assertIsNone(group_friend)
# endregion



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

    # 获取对方信息
    def test_get_friend_by_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token,
            "conversation": 114514
        }
        
        url = '/user/get_friend_by_conversation/'
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            'code': 2, 
            'info': 'Conversation does not exist', 
        })

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

class GroupInvitationTestCasebyAdmin(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.user3 = User.objects.create(name="user3", password=make_password("password"))
        self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
        self.group_conversation.members.add(self.user1, self.user2)
        self.group_conversation.administrators.add(self.user1)

    def test_admin_invite_member(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [self.user3.user_id],
            "token": token
        }
        response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Invited"], True)

        self.assertTrue(self.user3 in self.group_conversation.members.all())

    def test_admin_invite_member_group_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": 999,
            "invitee": [self.user3.user_id],
            "token": token
        }
        response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "Group does not exist")

    def test_admin_invite_member_permission_denied(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [self.user3.user_id],
            "token": token
        }
        response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 5)
        self.assertEqual(response.json()["info"], "Permission denied")

    def test_admin_invite_member_invitee_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [999],
            "token": token
        }
        response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 3)
        self.assertEqual(response.json()["info"], "The user you tried to invite does not exist")

    def test_admin_invite_member_user_already_in_group(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [self.user2.user_id],
            "token": token
        }
        response = self.client.post("/user/admin_invite_member/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 4)
        self.assertEqual(response.json()["info"], "User is already in the group")

class InviteMemberToGroupTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
        self.group_conversation.members.add(self.user1)

    def test_invite_member_to_group(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [self.user2.user_id],
            "token": token
        }
        response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Invited"], True)

    def test_invite_member_to_group_group_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": 999,
            "invitee": [self.user2.user_id],
            "token":token
        }
        response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "Group does not exist")

    def test_invite_member_to_group_invitee_not_exist(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [999],
            "token": token
        }
        response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 3)
        self.assertEqual(response.json()["info"], "The user you tried to invite does not exist")

    def test_invite_member_to_group_user_already_in_group(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "invitee": [self.user1.user_id],
            "token": token
        }
        response = self.client.post("/user/invite_member_to_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 4)
        self.assertEqual(response.json()["info"], "User is already in the group")

class GetGroupInvitationsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False)
        self.group_conversation.members.add(self.user1)
        self.group_invitation = GroupInvitation.objects.create(inviter_id=self.user2.user_id, invitee_id=self.user1.user_id, group_id=self.group_conversation.conversation_id)

    def test_get_group_invitations(self):
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
        response = self.client.post("/user/get_group_invitations/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return_data = response.json()
        invitations = return_data["invitations"]
        self.assertEqual(len(invitations), 1)

        invitation = invitations[0]
        self.assertEqual(invitation["invitation_id"], self.group_invitation.invitation_id)
        self.assertEqual(invitation["inviter_id"], self.user2.user_id)
        self.assertEqual(invitation["inviter_name"], self.user2.name)
        self.assertEqual(invitation["inviter_avatar"], self.user2.avatar)
        self.assertEqual(invitation["invitee_id"], self.user1.user_id)
        self.assertEqual(invitation["invitee_name"], self.user1.name)
        self.assertEqual(invitation["invitee_avatar"], self.user1.avatar)

    def test_get_group_invitations_group_not_exist(self):
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
        response = self.client.post("/user/get_group_invitations/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "Group does not exist")

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

class GroupConversationTestCase1(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.user3 = User.objects.create(name="user3", password=make_password("password"))
        self.group_conversation = Conversation.objects.create(conversation_name="Group Chat", is_Private=False, owner=self.user1.user_id)
        self.group_conversation.members.add(self.user1, self.user2, self.user3)

    def test_add_administrators(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "admins": [self.user2.user_id, self.user3.user_id],
            "token": token
        }
        response = self.client.post("/user/add_administrators/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Added"], True)

        updated_conversation = Conversation.objects.filter(conversation_id=self.group_conversation.conversation_id).first()
        self.assertTrue(self.user2 in updated_conversation.administrators.all())
        self.assertTrue(self.user3 in updated_conversation.administrators.all())

    def test_remove_administrator(self):
        self.group_conversation.administrators.add(self.user2, self.user3)
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "admin": [self.user2.user_id],
            "token": token
        }
        response = self.client.post("/user/remove_administrator/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Removed"], True)

        updated_conversation = Conversation.objects.filter(conversation_id=self.group_conversation.conversation_id).first()
        self.assertTrue(self.user2 not in updated_conversation.administrators.all())
        self.assertTrue(self.user3 in updated_conversation.administrators.all())

class GroupConversationTestCase2(TestCase):
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

    def test_set_validation_add_valid_member(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "conversation": self.group_conversation.conversation_id,
            "valid": "True",
            "token": token
        }
        response = self.client.post("/user/set_validation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Modified"], True)
        
    def test_set_validation_remove_valid_member(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        self.group_conversation.valid_members.add(self.user1)
        data = {
            "conversation": self.group_conversation.conversation_id,
            "valid": "False",
            "token": token
        }
        response = self.client.post("/user/set_validation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Modified"], True)

    def test_secondary_validate_correct_password(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "password": "password",
            "token": token
        }
        response = self.client.post("/user/secondary_validate/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Valid"], True)

    def test_secondary_validate_wrong_password(self):
        data = {
            "name": "user2",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "password": "wrong_password",
            "token": token
        }
        response = self.client.post("/user/secondary_validate/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
        self.assertEqual(response.json()["info"], "密码错误")

    def test_remove_member_from_group(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "members": [self.user2.user_id],
            "token": token
        }
        response = self.client.post("/user/remove_member_from_group/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Removed"], True)

        updated_conversation = Conversation.objects.filter(conversation_id=self.group_conversation.conversation_id).first()
        self.assertTrue(self.user2 not in updated_conversation.members.all())


    def test_set_group_announcement(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "announcement": "Welcome to our group!",
            "token": token
        }
        response = self.client.post("/user/set_group_announcement/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Set"], True)

        updated_conversation = Conversation.objects.filter(conversation_id=self.group_conversation.conversation_id).first()
        self.assertEqual(updated_conversation.announcement, "Welcome to our group!")

    def test_get_group_announcement(self):
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
        response = self.client.post("/user/get_group_announcement/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Announcement"], "")

        # Set the group announcement
        self.group_conversation.announcement = "Welcome to our group!"
        self.group_conversation.save()

        response = self.client.post("/user/get_group_announcement/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Announcement"], "Welcome to our group!")

    def test_get_group_owner(self):
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
        response = self.client.post("/user/get_group_owner/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["owner"]["id"], self.user1.user_id)

    def test_get_group_administrators(self):
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
        response = self.client.post("/user/get_group_administrators/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["administrators"]), 1)
        self.assertEqual(response.json()["administrators"][0]["id"], self.user1.user_id)

    def test_get_group_members(self):
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
        response = self.client.post("/user/get_group_members/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["members"]), 1)
        self.assertEqual(response.json()["members"][0]["id"], self.user2.user_id)

    def test_get_member_status(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "group": self.group_conversation.conversation_id,
            "member": self.user1.user_id,
            "token": token
        }
        response = self.client.post("/user/get_member_status/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["is_admin"], True)
        self.assertEqual(response.json()["is_owner"], True)

    def test_get_sig(self):
        data = {
            "name": "user1",
            "password": "password",
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        response = self.client.post("/user/get_sig/",{"token":token}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("sig" in response.json())


class StickyConversationTestCase1(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.user3 = User.objects.create(name="user3", password=make_password("password"))
        addFriends(self.user1, self.user2)
        addFriends(self.user1, self.user3)
        self.conversation = Conversation.objects.create(is_Private=True)
        self.conversation.members.add(self.user1, self.user2)
        
    def test_set_sticky_conversation_set(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        # Set sticky to True
        data = {
            "conversation": self.conversation.conversation_id,
            "sticky": "True",
            "token": token
        }
        response = self.client.post("/user/set_sticky_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Revised"], True)

    def test_set_sticky_conversation_remove(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Set sticky to False
        data = {
            "conversation": self.conversation.conversation_id,
            "sticky": "False",
            "token": token
        }
        response = self.client.post("/user/set_sticky_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["Revised"], True)

    def test_set_sticky_conversation_invalid_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "conversation": 999,
            "sticky": "True",
            "token": token
        }
        response = self.client.post("/user/set_sticky_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 2)
              
class StickyConversationTestCase2(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.user3 = User.objects.create(name="user3", password=make_password("password"))
        addFriends(self.user1, self.user2)
        addFriends(self.user1, self.user3)
        self.private_conversation = Conversation.objects.create(is_Private=True)
        self.private_conversation.members.add(self.user1, self.user2, self.user3)
        self.private_conversation.sticky_members.add(self.user1)
        self.group_conversation = Conversation.objects.create(is_Private=False)
        self.group_conversation.members.add(self.user1, self.user2, self.user3)
        self.group_conversation.sticky_members.add(self.user1)

    def test_get_sticky_private_conversations(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Get sticky private conversations
        data = {
            "token": token
        }
        response = self.client.post("/user/get_sticky_private_conversations/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        conversations = response.json()["conversations"]
        self.assertEqual(len(conversations), 1)
        conversation = conversations[0]
        self.assertEqual(conversation["id"], self.private_conversation.conversation_id)
        self.assertEqual(conversation["friend_id"], self.user2.user_id)
        self.assertEqual(conversation["friend_name"], self.user2.name)
        self.assertEqual(conversation["friend_avatar"], self.user2.avatar)
        self.assertTrue(conversation["is_Private"])
        self.assertFalse(conversation["silent"])
        self.assertTrue(conversation["sticked"])
        self.assertFalse(conversation["disabled"])
        self.assertFalse(conversation["validation"])

    def test_get_sticky_group_conversations(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Get sticky group conversations
        data = {
            "token": token
        }
        response = self.client.post("/user/get_sticky_group_conversations/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        conversations = response.json()["conversations"]
        self.assertEqual(len(conversations), 1)
        conversation = conversations[0]
        self.assertEqual(conversation["id"], self.group_conversation.conversation_id)
        self.assertEqual(conversation["name"], self.group_conversation.conversation_name)
        self.assertEqual(conversation["avatar"], self.group_conversation.conversation_avatar)
        self.assertFalse(conversation["is_Private"])
        self.assertFalse(conversation["silent"])
        self.assertTrue(conversation["sticked"])
        self.assertFalse(conversation["disabled"])
        self.assertFalse(conversation["validation"])

class UnreadMessageTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.conversation = Conversation.objects.create()
        self.conversation.members.add(self.user1, self.user2)
        self.message1 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id)
        self.message2 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id)
        self.message3 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id)
        self.message4 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id)
        self.message5 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id)
        self.message6 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id)
        self.message7 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id)
        self.message8 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id)

    def test_get_unread_messages(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Get unread messages
        data = {
            "conversation": self.conversation.conversation_id,
            "token": token
        }
        response = self.client.post("/user/get_unread_messages/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_set_read_message(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Set read messages
        data = {
            "conversation": self.conversation.conversation_id,
            "msg_id": self.message5.msg_id,
            "token": token
        }
        response = self.client.post("/user/set_read_message/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Set Read Messages': True})

        # Check if the messages are marked as read
        message_ids = [self.message1.msg_id, self.message2.msg_id, self.message3.msg_id,
                       self.message4.msg_id, self.message5.msg_id]
        for message_id in message_ids:
            message = Message.objects.get(msg_id=message_id)
            self.assertTrue(self.user1 in message.read_members.all())

class SilentConversationTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.conversation = Conversation.objects.create()
        self.conversation.members.add(self.user1, self.user2)

    def test_set_silent_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Set conversation to silent
        data = {
            "conversation": self.conversation.conversation_id,
            "silent": "True",
            "token": token
        }
        response = self.client.post("/user/set_silent_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Modified': True})

        # Check if the user is in the silent members list
        conversation = Conversation.objects.get(conversation_id=self.conversation.conversation_id)
        self.assertTrue(self.user1 in conversation.silent_members.all())

        # Unset conversation from silent
        data = {
            "conversation": self.conversation.conversation_id,
            "silent": "False",
            "token": token
        }
        response = self.client.post("/user/set_silent_conversation/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Modified': True})

        # Check if the user is removed from the silent members list
        conversation = Conversation.objects.get(conversation_id=self.conversation.conversation_id)
        self.assertFalse(self.user1 in conversation.silent_members.all())

class QueryAllRecordsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.conversation = Conversation.objects.create()
        self.conversation.members.add(self.user1, self.user2)

    def test_query_all_records(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Add some messages to the conversation
        message1 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id, msg_body="Hello")
        message2 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id, msg_body="Hi")

        # Query all records
        data = {
            "conversation": self.conversation.conversation_id,
            "token": token
        }
        response = self.client.post("/user/query_all_records/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages
        self.assertEqual(len(returned_messages), 2)
        self.assertEqual(returned_messages[0]["msg_id"], message1.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user1.user_id)
        self.assertEqual(returned_messages[0]["msg_body"], "Hello")
        self.assertEqual(returned_messages[1]["msg_id"], message2.msg_id)
        self.assertEqual(returned_messages[1]["sender_id"], self.user2.user_id)
        self.assertEqual(returned_messages[1]["msg_body"], "Hi")

class QueryRecordsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.conversation = Conversation.objects.create()
        self.conversation.members.add(self.user1, self.user2)
        self.message1 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id, msg_body="Hello")
        self.message2 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id, msg_body="Hi")

    def test_query_forward_records(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Query forward records
        data = {
            "msgidlist": [self.message1.msg_id, self.message2.msg_id],
            "token": token
        }
        response = self.client.post("/user/query_forward_records/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages
        self.assertEqual(len(returned_messages), 2)
        self.assertEqual(returned_messages[0]["msg_id"], self.message1.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user1.user_id)
        self.assertEqual(returned_messages[0]["msg_body"], "Hello")
        self.assertEqual(returned_messages[1]["msg_id"], self.message2.msg_id)
        self.assertEqual(returned_messages[1]["sender_id"], self.user2.user_id)
        self.assertEqual(returned_messages[1]["msg_body"], "Hi")

    def test_query_by_sender(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Query by sender
        data = {
            "conversation": self.conversation.conversation_id,
            "sender": self.user1.user_id,
            "token": token
        }
        response = self.client.post("/user/query_by_sender/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages
        self.assertEqual(len(returned_messages), 1)
        self.assertEqual(returned_messages[0]["msg_id"], self.message1.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user1.user_id)
        self.assertEqual(returned_messages[0]["msg_body"], "Hello")

    def test_query_by_content(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Query by content
        data = {
            "conversation": self.conversation.conversation_id,
            "content": "Hi",
            "token": token
        }
        response = self.client.post("/user/query_by_content/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages
        self.assertEqual(len(returned_messages), 1)
        self.assertEqual(returned_messages[0]["msg_id"], self.message2.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user2.user_id)
        self.assertEqual(returned_messages[0]["msg_body"], "Hi")

class QueryByTypeTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.conversation = Conversation.objects.create()
        self.conversation.members.add(self.user1, self.user2)
        self.message1 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id, is_image=True)
        self.message2 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id, is_video=True)
        self.message3 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id, is_file=True)
        self.message4 = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user2.user_id, is_audio=True)

    def test_query_by_type(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Query by type (image)
        data = {
            "conversation": self.conversation.conversation_id,
            "type": "image",
            "token": token
        }
        response = self.client.post("/user/query_by_type/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages with the specified type
        self.assertEqual(len(returned_messages), 1)
        self.assertEqual(returned_messages[0]["msg_id"], self.message1.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user1.user_id)
        self.assertTrue(returned_messages[0]["is_image"])
        self.assertFalse(returned_messages[0]["is_video"])
        self.assertFalse(returned_messages[0]["is_file"])
        self.assertFalse(returned_messages[0]["is_audio"])

        # Query by type (video)
        data = {
            "conversation": self.conversation.conversation_id,
            "type": "video",
            "token": token
        }
        response = self.client.post("/user/query_by_type/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages with the specified type
        self.assertEqual(len(returned_messages), 1)
        self.assertEqual(returned_messages[0]["msg_id"], self.message2.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user2.user_id)
        self.assertFalse(returned_messages[0]["is_image"])
        self.assertTrue(returned_messages[0]["is_video"])
        self.assertFalse(returned_messages[0]["is_file"])
        self.assertFalse(returned_messages[0]["is_audio"])

        # Query by type (file)
        data = {
            "conversation": self.conversation.conversation_id,
            "type": "file",
            "token": token
        }
        response = self.client.post("/user/query_by_type/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages with the specified type
        self.assertEqual(len(returned_messages), 1)
        self.assertEqual(returned_messages[0]["msg_id"], self.message3.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user1.user_id)
        self.assertFalse(returned_messages[0]["is_image"])
        self.assertFalse(returned_messages[0]["is_video"])
        self.assertTrue(returned_messages[0]["is_file"])
        self.assertFalse(returned_messages[0]["is_audio"])

        # Query by type (audio)
        data = {
            "conversation": self.conversation.conversation_id,
            "type": "audio",
            "token": token
        }
        response = self.client.post("/user/query_by_type/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_messages = response.json()["messages"]

        # Check if the returned messages match the added messages with the specified type
        self.assertEqual(len(returned_messages), 1)
        self.assertEqual(returned_messages[0]["msg_id"], self.message4.msg_id)
        self.assertEqual(returned_messages[0]["sender_id"], self.user2.user_id)
        self.assertFalse(returned_messages[0]["is_image"])
        self.assertFalse(returned_messages[0]["is_video"])
        self.assertFalse(returned_messages[0]["is_file"])
        self.assertTrue(returned_messages[0]["is_audio"])

class MessageDetailsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(name="user1", password=make_password("password"))
        self.user2 = User.objects.create(name="user2", password=make_password("password"))
        self.conversation = Conversation.objects.create()
        self.message = Message.objects.create(conversation_id=self.conversation.conversation_id, sender_id=self.user1.user_id)
        self.message.mentioned_members.add(self.user2)
        self.message.read_members.add(self.user1, self.user2)

    def test_get_mentioned_members(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Get mentioned members
        data = {
            "msg_id": self.message.msg_id,
            "token": token
        }
        response = self.client.post("/user/get_mentioned_members/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_members = response.json()["mentioned_members"]

        # Check if the returned members match the added mentioned members
        self.assertEqual(len(returned_members), 1)
        self.assertEqual(returned_members[0]["name"], self.user2.name)
        self.assertTrue(returned_members[0]["read"])
        self.assertEqual(returned_members[0]["avatar"], self.user2.avatar)

    def test_get_read_members(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]

        # Get read members
        data = {
            "msg_id": self.message.msg_id,
            "token": token
        }
        response = self.client.post("/user/get_read_members/", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        returned_members = response.json()["read_members"]

        # Check if the returned members match the added read members
        self.assertEqual(len(returned_members), 2)
        self.assertEqual(returned_members[0]["name"], self.user1.name)
        self.assertEqual(returned_members[0]["avatar"], self.user1.avatar)
        self.assertEqual(returned_members[1]["name"], self.user2.name)
        self.assertEqual(returned_members[1]["avatar"], self.user2.avatar)

