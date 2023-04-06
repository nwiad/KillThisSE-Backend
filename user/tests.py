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
            name="testuser",
            password=make_password("testpassword")
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserViewSet()
        client = Client()
        # Set a cookie
        client.cookies['my_cookie'] = 'cookie_value'
        client.cookies['session'] = 'session_value'
        

    # register
    # 正常注册
    def test_successful_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "newpassword"
        }
        request = self.client.post(reverse("user-register"), data=request_data)
        response = self.view.register(request)
        response_content = json.loads(response.content)
        expected_content = {"code": 0, "info": "Succeed", "isCreate": True}
        self.assertEqual(response_content, expected_content)
        self.assertTrue(User.objects.filter(name="testuser").exists())

    # 重复注册
    def test_duplicate_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword"
        }
        request = self.client.post(reverse("user-register"), data=request_data)
        response = self.view.register(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(name="testuser", password=make_password("testpassword")).exists())

    # 非法用户名
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser12345678901234567890",
            "password": "testpassword"
        }
        request = self.client.post(reverse("user-register"), data=request_data)
        print(request)
        print("1234554321")
        response = self.view.register(request)
        print(response)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertEqual(response_data, {"code": 1, "info": 'Illegal username'})

    # login
    # 正常登录
    def test_successful_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword"
        }
        request = self.client.post('/user/login/', json.dumps(request_data), content_type='application/json')
        response = self.view.login(request)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, {"Logged in": True})
        

    # 错误密码
    def test_wrong_password_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "wrongpassword"
        }
        request = self.client.post('/user/login/', json.dumps(request_data), content_type='application/json')
        
        response = self.view.login(request)
        self.assertEqual(response.status_code, 400)
        # self.assertIn("Wrong password", response.content.decode())
    
    # 试图登录不存在的用户
    def test_nonexsit_user_login(self):
        request_data = {
            "name": "nonexsitentuser",
            "password": "testpassword"
        }
        request = self.client.post('/user/login/', json.dumps(request_data), content_type='application/json')
        response = self.view.login(request)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertJSONEqual(response_data, {"code": 2, 'info': 'User does not exist'})

    # retrieve
    def test_retrieve_users(self):
        request = self.client.get('/users/')
        response = self.view.users(request)
        self.assertEqual(response.status_code, 200)
        # self.assertIn("users", response.content.decode())

    # logout
    def test_successful_logout(self):
        # Create a test user and log in
        user_data = {'name': 'testuser', 'password': 'testpassword'}
        response = self.client.post(reverse('user-register'), user_data, format='json')
        # self.assertEqual(response.status_code, 200)
        
        login_data = {'name': 'testuser', 'password': 'testpassword'}
        request = self.client.post('/user/login/', json.dumps(login_data), content_type='application/json')
        self.assertEqual(request.status_code, 200)

        # Log out
        response = self.client.post(reverse('logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'Logged out': True})

        
    # modify
    def test_modify(self):
        # 创建一个新用户并登录
        # client = Client()
        user_data = {'name': 'testuser', 'password': 'testpassword1'}
        response = self.client.post(reverse('user-register'), user_data, format='json')
        user = User.objects.get(name='testuser')
        self.assertEqual(response.status_code, 200)
        self.client.login(username="testuser", password="testpassword")

        # 修改用户名、密码和头像
        response = self.client.post(
            "/api/user/modify/",
            {
                "name": "newtestuser",
                "password": "newtestpassword",
                "avatar": "new_avatar",
            },
        )
        self.assertEqual(response.status_code, 200)

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.name, "newtestuser")
        self.assertTrue(user.check_password("newtestpassword"))
        self.assertEqual(user.avatar, "new_avatar")

    # friend
    # send_friend_request
    def test_send_friend_request(self):
        # 创建两个新用户并登录
        # client = Client()
        user_data = {'name': 'testuser1', 'password': 'testpassword1'}
        response = self.client.post(reverse('user-register'), user_data, format='json')
        user_data = {'name': 'testuser2', 'password': 'testpassword2'}
        response = self.client.post(reverse('user-register'), user_data, format='json')

        login_data = {'name': 'testuser1', 'password': 'testpassword1'}
        request = self.client.post('/user/login/', json.dumps(login_data), content_type='application/json')
        self.assertEqual(request.status_code, 200)

        self.client.login(username="testuser1", password="testpassword1")
        
        # 获取用户对象
        user1 = User.objects.get(name='testuser1')
        user2 = User.objects.get(name='testuser2')

        # 发送好友请求
        response = self.client.post(
            "/api/user/send_friend_request/", {"friend_user_id": user2.user_id}
        )
        self.assertEqual(response.status_code, 200)

        # 检查好友请求是否已发送
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)

    # respond_friend_request
    def test_respond_friend_request(self):
        # 创建两个新用户并登录
        # client = Client()
        user_data = {'name': 'testuser1', 'password': 'testpassword1'}
        response = self.client.post(reverse('user-register'), user_data, format='json')
        user_data = {'name': 'testuser2', 'password': 'testpassword2'}
        response = self.client.post(reverse('user-register'), user_data, format='json')

        login_data = {'name': 'testuser1', 'password': 'testpassword1'}
        request = self.client.post('/user/login/', json.dumps(login_data), content_type='application/json')
        self.assertEqual(request.status_code, 200)

        self.client.login(username="testuser1", password="testpassword1")
        
        # 获取用户对象
        user1 = User.objects.get(name='testuser1')
        user2 = User.objects.get(name='testuser2')

        # 发送好友请求
        response = client.post(
            "/api/user/send_friend_request/", {"friend_user_id": user2.user_id}
        )
        
        sendFriendRequest(user1, user2) 
        
        # 登录第二个用户
        
        client = Client()
        client.login(username="testuser2", password="testpassword2")

        # 接受好友请求
        response = client.post(
            "/api/user/respond_friend_request/",
            {"friend_user_id": user1.user_id, "response": "accept"},
        )
        self.assertEqual(response.status_code, 200)

        # 检查用户是否已成为好友
        are_friends = isFriend(user1, user2)
        self.assertTrue(are_friends)
    
    # users
    def test_users(self):
        # 创建两个新用户
        # client = Client()
        user_data = {'name': 'testuser1', 'password': 'testpassword1'}
        response = self.client.post(reverse('user-register'), user_data, format='json')
        user_data = {'name': 'testuser2', 'password': 'testpassword2'}
        response = self.client.post(reverse('user-register'), user_data, format='json')

        # 获取用户列表并检查状态代码是否为200
        response = self.client.get("/api/user/users/")
        # self.assertEqual(response.status_code, 200)

        # 检查返回的用户列表是否正确
        response_content = json.loads(response.content)
        self.assertEqual(len(response_content["users"]), 2)

'''
0406 测试用例涵盖的功能

用户注册

    正常注册
    重复注册
    非法用户名
    用户登录

正常登录
    错误密码
    试图登录不存在的用户
    获取用户列表

用户登出

修改用户信息

好友功能

发送好友请求
响应好友请求（接受）
'''