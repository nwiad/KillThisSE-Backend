import json
from django.test import TestCase, RequestFactory
from django.contrib.auth.hashers import make_password
from user.models import User
from user.views import startup, user_register, user_login, users

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

    def test_startup(self):
        request = self.factory.get('/startup/')
        response = startup(request)
        self.assertEqual(response.status_code, 200)
        # self.assertJSONEqual(response.content, {"message": "There is no exception in this library"})
        self.assertIn("message", response.content.decode())

    # register
    # 正常注册
    def test_successful_user_registration(self):
        request_data = {
            "name": "newuser",
            "password": "newpassword",
        }
        request = self.factory.post('/user/register/', json.dumps(request_data), content_type='application/json')
        response = user_register(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '{"code": 0, "info": "Succeed", "isCreate": true}')
        self.assertTrue(User.objects.filter(name="newuser").exists())

    # 重复注册
    def test_duplicate_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword",
        }
        request = self.factory.post('/user/register/', json.dumps(request_data), content_type='application/json')
        response = user_register(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(name="testuser", password=make_password("testpassword")).exists())

    # 非法用户名
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser12345678901234567890",
            "password": "testpassword",
        }
        request = self.factory.post('/user/register/', json.dumps(request_data), content_type='application/json')
        response = user_register(request)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"code": 1, "info": '不合法的用户名'})

    
    # login
    # 正常登录
    def test_successful_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword",
        }
        request = self.factory.post('/user/login/', json.dumps(request_data), content_type='application/json')
        response = user_login(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logged in", response.content.decode())

    # 错误密码
    def test_wrong_password_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "wrongpassword",
        }
        request = self.factory.post('/user/login/', json.dumps(request_data), content_type='application/json')
        response = user_login(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Wrong password", response.content.decode())
    
    # 试图登录不存在的用户
    def test_nonexsit_user_login(self):
        request_data = {
            "name": "nonexsitentuser",
            "password": "testpassword",
        }
        request = self.factory.post('/user/login/', json.dumps(request_data), content_type='application/json')
        response = user_login(request)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"code": 2, 'info': 'User does not exist'})

    # retrieve
    def test_retrieve_users(self):
        request = self.factory.get('/users/')
        response = users(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.content.decode())

