import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.hashers import make_password
from user.models import User, FriendshipRequest, Group, GroupFriend, Friendship
from msg.models import Conversation, Message
from user.views import UserViewSet
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
from django.urls import reverse
from unittest.mock import patch


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
      
        
# region register
# 版本一 无邮箱验证
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
        self.assertEqual(response_content, {"code": 1, "info": "Illegal username"})

    # 重复注册
    def test_duplicate_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword"
        }
        response = register_try(self, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(name="testuser", password=make_password("testpassword")).exists())
        self.assertEqual(response.content, b'{"code": 2, "info": "Username already exists"}')
        
    # 非法密码
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser123",
            "password": "tes"
        }
        response = register_try(self, request_data)
        self.assertEqual(response.status_code, 400)
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 3, "info": "Illegal password"})

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

# 版本2 有邮箱验证
    # 发邮件
    def test_send_email_for_register(self):
        # Make a POST request to the send_email_for_register endpoint
        data = {
            'name': 'testuseree',
            'password': 'testpasswordee',
            'email': 'testuser@example.com'
        }
        response = self.client.post('/user/send_email_for_register/', data=data, content_type="application/json")

        # Check that the response status code is 200 and the user was created with a code
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(name='testuseree').exists())
        self.assertTrue(response.json()['send'])
        self.assertEqual(User.objects.get(name='testuseree').user_code, response.json()['code_send'])

    def test_register_success(self):
        # Create a user in the database with a code
        user = User.objects.create(
            name='testuser22',
            password=make_password('testpassword22'),
            user_email='testuser@example.com',
            user_code=123456
        )

        # Make a POST request to the register endpoint with the correct code
        data = {
            'name': 'testuser22',
            'code_input': 123456
        }
        response = self.client.post('/user/register/', data=data, content_type="application/json")

        # Check that the response status code is 200 and the user was successfully created
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'Created': True, 'code': 0, 'info': 'Succeed'})

    def test_register_wrong_code(self):
        # Create a user in the database with a code
        user = User.objects.create(
            name='testuser33',
            password=make_password('testpassword33'),
            user_email='testuser@example.com',
            user_code=123456
        )
        data = {
            'name': 'testuser33',
            'code_input': '654321'
        }
        # Make a POST request to the register endpoint with the wrong code
        response = self.client.post('/user/register/', data=data, content_type="application/json")
        
        # Check that the response status code is 200 and the user was deleted
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code': 5, 'info': 'Wrong verification code'})
        # 创建失败，用户被删除
        self.assertFalse(User.objects.filter(name='testuser33').exists())

# endregion


# region login
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
        self.assertEqual(response.content, b'{"code": 1, "info": "Illegal username"}')
    
    
    # 试图登录不存在的用户
    def test_nonexsit_user_login(self):
        non_data = {
            "name": "nonexsitentuser",
            "password": "testpassword"
        }
            
        response = login_try(self, non_data)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, {"code": 2, "info": "User does not exist"})
    
    # 错误密码
    def test_wrong_password_user_login(self):
        wp_data = {
            "name": "testuser",
            "password": "wrongpassword"
        }
        response = login_try(self, wp_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'{"code": 3, "info": "Wrong password"}')
       
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


# region modify
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
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 1, "info": "Not logged in"})

        # 3 username already exists
        response = self.client.post(
            RESETNAME,
            {
                "name": "newtestuser",
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 1, "info": "Not logged in"})

    def test_send_email_for_changepwd(self):
        # Make a POST request to the send_email_for_changepwd endpoint
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        data = {
            'old_pwd': '12345678',
            "token": token
        }
        response = self.client.post('/user/send_email_for_changepwd/', 
                                    data=data,
                                    content_type="application/json")
        # Check that the response status code is 200 and the user code was updated
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['Sent'])
    
    def test_reset_password(self):
        # Make a POST request to the reset_password endpoint
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        user = User.objects.get(name="testuser")
        data = {
            'old_pwd': '12345678',
            "token": token
        }
        # 假装填入了正确验证码
        user.user_code = 123456
        user.save()
        data = {
            'new_pwd': 'newpassword',
            "token": token,
            'code_input': 123456
            }
        response = self.client.post('/user/reset_password/', data=data, content_type="application/json")
        
        # Check that the response status code is 200 and the user password was updated
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(name='testuser').check_password('newpassword'))
        
    def test_reset_password_correct_code(self):
                # Make a POST request to the reset_password endpoint
        login_data = {
            "name": "testuser", 
            "password": "12345678"
            }
        response = login_someone(self, login_data)
        token = response.json()["Token"]
        
        user = User.objects.get(name="testuser")
        data = {
            'old_pwd': '12345678',
            "token": token
        }
        # 假装填入了错误验证码
        user.user_code = 123488
        user.save()
        data = {
            'new_pwd': 'newpassword',
            "token": token,
            'code_input': 123456
            }
        response = self.client.post('/user/reset_password/', data=data, content_type="application/json")
        
        # Check that the response status code is 200 and the user password was updated
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.get(name='testuser').check_password('12345678'))
        self.assertFalse(User.objects.get(name='testuser').check_password('newpassword'))
   
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
    
    
# region friend add
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
        self.assertEqual(response.json(), {"code": 1, "info": "target Friend not exist"})
        
        
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
        self.assertEqual(response.json(), {"code": 3, "info": "Request already exists"})


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
        self.assertEqual(response.json(), {"code": 2, "info": "Already become friends"})
        
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
  
  
# region friend del
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
        self.assertEqual(response.json(), {"code": 2, "info": "your Friend not exist"})
        
        # 删除非好友
        data={
            "friend_user_id": user.user_id,
            "token":token
        }
        response = delf(self, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 3, "info": "Not your friend"})
        
        user.delete()
        friend.delete()

    def test_get_profile(self):
        # 创建测试用户
        user = User.objects.create(name="test_user", password=make_password("password"))
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
        self.assertEqual(response.json(), {
            "code": 0,
            "info": "Succeed",
            "user_id": user.user_id,
            "name": user.name,
            "avatar": user.avatar
        })
        
        # 删除测试用户
        user.delete()
# endregion


# region search user 
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
        self.assertEqual(response.json(), {"code":2, "info": "User searched by id not exist"})
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
        self.assertEqual(response.json(), {"code":2, "info": "User searched by name not exist"})
        # 删除测试用户
        user.delete()
# endregion


# region search user in friend list
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

        self.assertEqual(response.json(),{"code": 2, "info": "Friend searched by id not exist"})
        
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

        self.assertEqual(response.json(),{"code": 2, "info": "Friend searched by name not exist"})
        
        
        userstanger = User.objects.create(name="stranger", password=make_password("password"))
        
        # 失败 非好友    
        data={
            "friend_name": userstanger.name,
            "token": token
        }
        response = sfbn(self, data)
        
        self.assertEqual(response.json(),{"code": 2, "info": "Friend you search not exist"})
        
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


# region  好友列表
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
   
        
# region 好友分组
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
# endregion
        

class ConversationTestCase(TestCase):
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
            "conversation_id": self.conversation.conversation_id
        })
        
        # Test successful create
        response = self.client.post(url, {'friend': self.user3.user_id, "token": token},content_type="application/json")

        self.assertEqual(response.status_code, 200)
        conversation = Conversation.objects.filter(members__in=[self.user1], is_Private=True).filter(members__in=[self.user3]).first()
        self.assertTrue(conversation is not None)
        self.assertEqual(response.json(), {
            'code': 0, 
            'info': 'Succeed',
            "conversation_id": conversation.conversation_id
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
         
    def create_group_conversation(self):
        pass
    
    def get_group_conversations(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token
        }
        url = "/user/get_group_conversations/"
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
    
    def create_group_conversation(self):
        data = {
            "name": "user1",
            "password": "password"
        }
        response = login_someone(self, data)
        token = response.json()["Token"]
        data = {
            "token": token,
            "members": [self.user2.user_id, self.user3.user_id]
        }
        
        url = "/user/create_group_conversation/"
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        