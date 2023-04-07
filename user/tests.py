import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.hashers import make_password
from user.models import User
from user.views import UserViewSet
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
from django.urls import reverse
from unittest.mock import patch

class UserViewTests(TestCase):
    # create a user object that is common across all test methods
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            name = "testuser", 
            password = make_password("123456")
            )
    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserViewSet()
        self.client = Client()
        # Set a cookie
        self.client.cookies['my_cookie'] = 'cookie_value'
        self.client.cookies['session'] = 'session_value'
        
    # register
    # 正常注册
    def test_successful_user_registration(self):
        request_data = {
            "name": "testuser0",
            "password": "newpassword0"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        response_content = json.loads(response.content)
        print(response_content)
        
        expected_content = {"code": 0, "info": "Succeed", "Created": True}
        self.assertEqual(response_content, expected_content)
        self.assertTrue(User.objects.filter(name="testuser0").exists())

    # 重复注册
    def test_duplicate_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword"
        }
        response = self.client.post(reverse("user-register"), data=request_data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(name="testuser", password=make_password("testpassword")).exists())

    # 非法用户名
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser12345678901234567890",
            "password": "testpassword"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        print(response.content)
        self.assertEqual(response.status_code, 400)

        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 1, "info": 'Illegal username'})

    # login
    # 正常登录
    def test_successful_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "123456"
            }
        response = self.client.post('/user/login/', data=request_data, content_type='application/json')
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {'code': 0, 'info': 'Succeed', "Logged in": True})
        
    # 错误密码
    def test_wrong_password_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post('/user/login/', json.dumps(request_data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Wrong password", response.content.decode())
    
    # 试图登录不存在的用户
    def test_nonexsit_user_login(self):
        request_data = {
            "name": "nonexsitentuser",
            "password": "testpassword"
        }
        response = self.client.post('/user/login/', json.dumps(request_data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, {"code": 2, "info": "User does not exist"})

    # retrieve
    def test_retrieve_users(self):
        request = self.client.get('/users/')
        response = self.view.users(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.content.decode())

    # logout
    def test_successful_logout(self):
        # log in
        login_data = {
            'name': 'testuser', 
            'password': '123456'
            }
        response = self.client.post('/user/login/', data=login_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Log out
        response = self.client.post(reverse('user-logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Logged out': True})
       
    # modify
    def test_modify(self):
        # 登录
        login_data = {
            'name': 'testuser', 
            'password': '123456'
            }
        response = self.client.post('/user/login/', data=login_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        user = User.objects.get(name='testuser')

        # 修改用户名、密码和头像
        response = self.client.post(
            "/user/modify/",
            {
                "name": "newtestuser",
                "password": "newtestpassword",
                "avatar": "new_avatar",
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.name, "newtestuser")
        self.assertTrue(user.password,make_password("newtestpassword"))
        self.assertEqual(user.avatar, "new_avatar")

    # friend
    # send_friend_request
    def test_send_friend_request(self):
        # 创建两个新用户并登录1
        request_data = {
            "name": "testuser1",
            "password": "newpassword1"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        request_data = {
            "name": "testuser2",
            "password": "newpassword2"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # 登录1
        login_data = {'name': 'testuser1', 'password': 'newpassword1'}
        response = self.client.post('/user/login/', json.dumps(login_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # response_content = self.client.login(username="testuser1", password="testpassword1")
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {'code': 0, 'info': 'Succeed', "Logged in": True})
        
        
        # 获取用户对象
        user1 = User.objects.get(name='testuser1')
        user2 = User.objects.get(name='testuser2')

        # 发送好友请求
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": user2.user_id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 检查好友请求是否已发送
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)

    # # respond_friend_request
    # def test_respond_friend_request(self):
    #     # 创建两个新用户并登录
    #             # 创建两个新用户并登录1
    #     request_data = {
    #         "name": "testuser1",
    #         "password": "newpassword1"
    #     }
    #     response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
    #     self.assertEqual(response.status_code, 200)
        
    #     request_data = {
    #         "name": "testuser2",
    #         "password": "newpassword2"
    #     }
    #     response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
    #     self.assertEqual(response.status_code, 200)

    #     login_data = {'name': 'testuser1', 'password': 'newpassword1'}
    #     response = self.client.post('/user/login/', json.dumps(login_data), content_type='application/json')
    #     self.assertEqual(response.status_code, 200)
        

    #     # 登录第一个用户
    #     self.client.login(username="testuser1", password="testpassword1")
    #     response_content = json.loads(response.content)
    #     self.assertEqual(response_content, {'code': 0, 'info': 'Succeed', "Logged in": True})
        
    #     # 获取用户对象
    #     user1 = User.objects.get(name='testuser1')
    #     user2 = User.objects.get(name='testuser2')

    #     # 发送好友请求
    #     response = self.client.post(
    #         "/user/send_friend_request/", 
    #         {"friend_user_id": user2.user_id},
    #         content_type='application/json'
    #     )
    #     self.assertEqual(response.status_code, 200)

    #     # 检查好友请求是否已发送
    #     request_sent = requestExists(user1, user2)
    #     self.assertTrue(request_sent)

    #     sendFriendRequest(user1, user2) # 数据库--发送好友请求
        
    #     # 登录第二个用户
    #     self.client.login(username="testuser2", password="testpassword2")

    #     # 接受好友请求
    #     response = self.client.post(
    #         "/user/respond_friend_request/",
    #         {"friend_user_id": user1.user_id, "response": "accept"},
    #         content_type='application/json'
    #     )
    #     self.assertEqual(response.status_code, 200)

    #     # 检查用户是否已成为好友
    #     are_friends = isFriend(user1, user2)
    #     self.assertTrue(are_friends)
    
#     # users
#     def test_users(self):
#         # 创建两个新用户
#         # client = Client()
#         user_data = {'name': 'testuser1', 'password': 'testpassword1'}
#         response = self.client.post(reverse('user-register'), user_data, format='json')
#         user_data = {'name': 'testuser2', 'password': 'testpassword2'}
#         response = self.client.post(reverse('user-register'), user_data, format='json')

#         # 获取用户列表并检查状态代码是否为200
#         response = self.client.get("/api/user/users/")
#         # self.assertEqual(response.status_code, 200)

#         # 检查返回的用户列表是否正确
#         response_content = json.loads(response.content)
#         self.assertEqual(len(response_content["users"]), 2)

# '''
# 0406 测试用例涵盖的功能

# 用户注册

#     正常注册
#     重复注册
#     非法用户名
#     用户登录

# 正常登录
#     错误密码
#     试图登录不存在的用户
#     获取用户列表

# 用户登出

# 修改用户信息

# 好友功能

# 发送好友请求
# 响应好友请求（接受）
# '''