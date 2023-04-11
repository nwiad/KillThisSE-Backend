import json
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.hashers import make_password
from user.models import User
from user.views import UserViewSet
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
from django.urls import reverse
from unittest.mock import patch

def login_someone(self, data):
    response = self.client.post('/user/login/', data=data, content_type='application/json')
    response_content = json.loads(response.content)
    self.assertEqual(response_content, {'code': 0, 'info': 'Succeed', "Logged in": True})
    return response

def login_try(self, data):
    response = self.client.post('/user/login/', data=data, content_type='application/json')
    return response

class UserViewTests(TestCase):
    # create a user object that is common across all test methods
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            name = "testuser", 
            password = make_password("12345678")
            )
        user00 = User.objects.create(name="user000", password=make_password("password000"))
        addFriends(cls.user, user00)
        
        
    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserViewSet()
        self.client = Client()
        # Set a cookie
        self.client.cookies['my_cookie'] = 'cookie_value'
        self.client.cookies['session'] = 'session_value'
      
        
#! register
    # 正常注册
    def test_successful_user_registration(self):
        request_data = {
            "name": "testuser0",
            "password": "newpassword0"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        response_content = json.loads(response.content)
        expected_content = {"code": 0, "info": "Succeed", "Created": True}
        self.assertEqual(response_content, expected_content)
        self.assertTrue(User.objects.filter(name="testuser0").exists())

    # 非法用户名
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser12345678901234567890",
            "password": "testpassword"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 1, "info": 'Illegal username'})

    # 重复注册
    def test_duplicate_user_registration(self):
        request_data = {
            "name": "testuser",
            "password": "testpassword"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(name="testuser", password=make_password("testpassword")).exists())
        self.assertEqual(response.content, b'{"code": 2, "info": "Username already exists"}')
        
    # 非法密码
    def test_illegal_user_registration(self):
        request_data = {
            "name": "testuser123",
            "password": "tes"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {"code": 3, "info": 'Illegal password'})

    # 注销账户
    def test_cancel_account(self):
        request_data = {
            "name": "testuser1",
            "password": "newpassword1"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        # log in user
        login_someone(self, request_data)
        
        response = self.client.post('/user/cancel_account/', data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"code": 0, "info": "Succeed", "Deleted": true}')
        
        

#! login
    # 正常登录
    def test_successful_user_login(self):
        request_data = {
            "name": "testuser",
            "password": "12345678"
            }
        
        login_someone(self, request_data)
        
        # 重复登录
        rep_data = {
            "name": "testuser",
            "password": "12345678"
            }
        response = login_try(self, rep_data)
        self.assertEqual(response.content, b'{"code": 4, "info": "Already logged in"}')
    
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
    
    # retrieve
    def test_retrieve_users(self):
        request = self.client.get('/users/')
        response = self.view.users(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.content.decode())

    # logout
    def test_successful_logout(self):
        # log in
        data = {
            "name": "testuser",
            "password": "12345678"
        }
        response = login_someone(self, data)
        self.assertEqual(response.status_code, 200)

        # Log out
        response = self.client.post(reverse('user-logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Logged out': True})
       
       
#! modify
    def test_reset_name(self):
        # log in
        login_data = {
            'name': 'testuser', 
            'password': '12345678'
            }
        response = login_someone(self, login_data)
        
        user = User.objects.get(name='testuser')

        # 修改用户名成功
        response = self.client.post(
            "/user/reset_name/",
            {
                "name": "newtestuser",
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Modified': True})

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.name, "newtestuser")


        # 2 illegal username
        response = self.client.post(
            "/user/reset_name/",
            {
                "name": "illegal!name",
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code': 2, 'info': 'Illegal username'})

        # 3 username already exists
        response = self.client.post(
            "/user/reset_name/",
            {
                "name": "newtestuser",
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"code": 3, "info": "Username already exists"})

    def test_reset_password(self):
        # log in
        login_data = {
            'name': 'testuser', 
            'password': '12345678'
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
        
        user = User.objects.get(name='testuser')

        # 修改密码失败 错误old
        response = self.client.post(
            "/user/reset_password/",
            {
                "old_pwd": "123428",
                "new_pwd": "newpassword",
            },
            content_type='application/json'
        )
        self.assertEqual(response.json(), {'code': 2, 'info': 'Wrong old password'})
        
        # 修改密码失败 错误new
        response = self.client.post(
            "/user/reset_password/",
            {
                "old_pwd": "12345678",
                "new_pwd": "new",
            },
            content_type='application/json'
        )
        self.assertEqual(response.json(), {'code': 3, 'info': 'Illegal new password'})

        # 修改密码
        response = self.client.post(
            "/user/reset_password/",
            {
                "old_pwd": "12345678",
                "new_pwd": "newpassword",
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        
         # 登出
        response = self.client.post(reverse('user-logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Logged out': True})

        # 清除session 登录另一个用户需要换session！
        self.client.cookies['session'] = 'session_value3'
        
        
        # 旧密码登录失败
        login_data = {
            'name': 'testuser', 
            'password': '12345678'
            }
        response = login_try(self, login_data)
        self.assertNotEqual(response.status_code, 200)
        
        self.client.cookies['session'] = 'session_value4'
        
        # 新密码登录成功
        login_data = {
            'name': 'testuser', 
            'password': 'newpassword'
            }
        response = login_someone(self, login_data)
        response_content = json.loads(response.content)
        self.assertEqual(response_content, {'code': 0, 'info': 'Succeed', "Logged in": True})
        
    def test_reset_avatar(self):
                # log in
        login_data = {
            'name': 'testuser', 
            'password': '12345678'
            }
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
        
        user = User.objects.get(name='testuser')

        # 修改头像
        response = self.client.post(
            "/user/reset_avatar/",
            {
                "avatar": "newavatar",
            },
            content_type='application/json'
        )
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Modified': True})
        self.assertEqual(response.status_code, 200)

        # 检查用户信息是否已经修改
        user.refresh_from_db()
        self.assertEqual(user.avatar, "newavatar")
    
    
#! friend add
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
        
        response = login_someone(self, login_data)
        self.assertEqual(response.status_code, 200)
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
        
        # 发送好友请求失败： 好友不存在
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": 999},
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 1, 'info': 'target Friend not exist'})
        
        
        # 发送好友请求失败： 重复发送
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": user2.user_id},
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 3, 'info': 'Request already exists'})


        # 登出
        response = self.client.post(reverse('user-logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Logged out': True})

        self.client.cookies['session'] = 'session_value5'

        # 登录2
        login_data = {'name': 'testuser2', 'password': 'newpassword2'}
        response = login_someone(self, login_data)
        
        # 2又向1 发送好友请求
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": user1.user_id},
            content_type='application/json'
        )
        response_content = json.loads(response.content)
        print(response_content)
        self.assertEqual(response_content, {'code': 0, 'info': 'Succeed', 'Become Friends successfully': True})
                
        # 清除session 登录另一个用户需要换session！
        self.client.cookies['session'] = 'session_value4'
        

        # testuser 和 user000 已经是好友
        # 登录1
        login_data = {'name': 'testuser', 'password': '12345678'}
        response = login_someone(self, login_data)
        
        user3 = User.objects.get(name='user000')
        
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": user3.user_id},
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 2, 'info': 'Already become friends'})
        
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
            'name': 'user1', 
            'password': 'password1'
            }
        login_someone(self, login_data)
        

        # test case: successfully get friend requests
        response = self.client.get('/user/get_friend_requests/')
        self.assertEqual(response.status_code, 200)
        
        print(response.json())
        self.assertEqual(response.json(), {
            'code': 0, 
            'info': 'Succeed',
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

        # # test case: no friend requests
        # FriendshipRequest.objects.all().delete()
        # response = self.client.get('/user/friend_requests/', **headers)
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.json(), {"requests": []})

        # # test case: invalid session id
        # headers['HTTP_SESSION_ID'] = 'invalid_session_id'
        # response = self.client.get('/user/friend_requests/', **headers)
        # self.assertEqual(response.status_code, 401)
        # self.assertEqual(response.json(), {"error_code": 1, "error_message": "Invalid session ID"})

    # respond_friend_request  ok
    def test_respond_friend_request(self):
        # 创建两个新用户
        request_data = {
            "name": "testuser11",
            "password": "newpassword11"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        request_data = {
            "name": "testuser22",
            "password": "newpassword22"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # 登录第一个用户
        login_data = {'name': 'testuser11', 'password': 'newpassword11'}
        response = login_someone(self, login_data)
        
        # 获取用户对象
        user1 = User.objects.get(name='testuser11')
        user2 = User.objects.get(name='testuser22')

        # 发送好友请求
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": user2.user_id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 检查好友请求是否已发送  参数1 向参数2发送的请求存在
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)

        # 登出
        response = self.client.post(reverse('user-logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Logged out': True})

        # 清除session 登录另一个用户需要换session！
        self.client.cookies['session'] = 'session_value2'
        
        # 登录第二个用户
        login_data = {'name': 'testuser22', 'password': 'newpassword22'}
        response = login_someone(self, login_data)
        
        # 接受好友请求
        response = self.client.post(
            "/user/respond_friend_request/",
            {
                "friend_user_id": user1.user_id, 
                "response": "accept"
                },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Become Friends': True})

        # 检查用户是否已成为好友
        are_friends = isFriend(user1, user2)
        self.assertTrue(are_friends)
    
    # respond_friend_request  no
    def test_respond_friend_request(self):
        # 创建两个新用户
        request_data = {
            "name": "testuser11",
            "password": "newpassword11"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        request_data = {
            "name": "testuser22",
            "password": "newpassword22"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # 登录第一个用户
        login_data = {'name': 'testuser11', 'password': 'newpassword11'}
        login_someone(self, login_data)
        
        # 获取用户对象
        user1 = User.objects.get(name='testuser11')
        user2 = User.objects.get(name='testuser22')

        # 发送好友请求
        response = self.client.post(
            "/user/send_friend_request/", 
            {"friend_user_id": user2.user_id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 检查好友请求是否已发送  参数1 向参数2发送的请求存在
        request_sent = requestExists(user1, user2)
        self.assertTrue(request_sent)

        # 登出
        response = self.client.post(reverse('user-logout'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Logged out': True})

        # 清除session 登录另一个用户需要换session！
        self.client.cookies['session'] = 'session_value2'
        
        # 登录第二个用户
        login_data = {'name': 'testuser22', 'password': 'newpassword22'}
        response = login_someone(self, login_data)
        
        # 接受好友请求
        response = self.client.post(
            "/user/respond_friend_request/",
            {
                "friend_user_id": user1.user_id, 
                "response": "reject"
                },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Become Friends': False})

        # 检查用户是否已成为好友
        are_friends = isFriend(user1, user2)
        self.assertFalse(are_friends)
    
    
#! friend del
    def test_del_friend(self):
        # 创建测试用户和好友
        user = User.objects.create(name="test_user", password=make_password("password"))
        friend = User.objects.create(name="test_friend", password=make_password("password"))
        
        # 创建好友关系
        addFriends(user, friend)
        
        # 登录user 
        login_data = {'name': 'test_user', 'password': 'password'}
        response = login_someone(self, login_data)
        
        # 模拟请求
        data={'friend_user_id': friend.user_id}
        response = self.client.post('/user/del_friend/', data=data, content_type='application/json')
  
        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'code': 0, 'info': 'Succeed', 'Deleted': True})
        
        # 确认好友关系已删除
        are_friends = isFriend(user, friend)
        self.assertFalse(are_friends)
        
        # 删除不存在的好友
        data={'friend_user_id': 999}
        response = self.client.post('/user/del_friend/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code': 2, 'info': 'your Friend not exist'})
        
        # 删除非好友
        data={'friend_user_id': user.user_id}
        response = self.client.post('/user/del_friend/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code': 3, 'info': 'Not your friend'})
        
        user.delete()
        friend.delete()

    def test_get_profile(self):
        # 创建测试用户
        user = User.objects.create(name="test_user", password=make_password("password"))
        # 登录user 
        login_data = {'name': 'test_user', 'password': 'password'}
        response = login_someone(self, login_data)
        
        # 模拟请求
        response = self.client.get('/user/get_profile/', content_type='application/json')
  
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

#! 全局搜索 
    # by id
    def test_search_by_id(self):
        # 创建测试用户
        user = User.objects.create(name="test_user", password=make_password("password"))
        
        # 登录user 
        login_data = {'name': 'test_user', 'password': 'password'}
        response = login_someone(self, login_data)
        
        teuser = User.objects.get(name="testuser")
        # 模拟请求 成功
        data={
            'friend_user_id': teuser.user_id,
        }
        response = self.client.post('/user/search_by_id/', data=data, content_type='application/json')

        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 
            {'code': 0, 
             'info': 'Succeed', 
             'user_id': teuser.user_id, 
             'name': teuser.name,
             'avatar': teuser.avatar
            })
        
        # 搜索无效id
        data={
            'friend_user_id': 999,
        }
        response = self.client.post('/user/search_by_id/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code':2, 'info': "User searched by id not exist"})
        # 删除测试用户
        user.delete()

    # by name
    def test_search_by_id(self):
        # 创建测试用户
        user = User.objects.create(name="test_user", password=make_password("password"))
        
        # 登录user 
        login_data = {'name': 'test_user', 'password': 'password'}
        response = login_someone(self, login_data)
        
        teuser = User.objects.get(name="testuser")
        # 模拟请求 成功
        data={
            'friend_name': teuser.name,
        }
        response = self.client.post('/user/search_by_name/', data=data, content_type='application/json')

        # 断言响应状态码和内容
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 
            {'code': 0, 
             'info': 'Succeed', 
             'user_id': teuser.user_id, 
             'name': teuser.name,
             'avatar': teuser.avatar
            })
        
        # 搜索无效id
        data={
            'friend_name': "99999",
        }
        response = self.client.post('/user/search_by_name/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code':2, 'info': "User searched by name not exist"})
        # 删除测试用户
        user.delete()

#! 好友范围搜索
    # by id
    def test_search_friend_by_id(self):
        # 登录user 
        login_data = {'name': 'testuser', 'password': '12345678'}
        login_someone(self, login_data)
        user01 = User.objects.get(name="testuser")
        user00 = User.objects.get(name="user000")
        # 失败
        data={
            'friend_id': 999
        }
        response = self.client.post('/user/search_friend_by_id/', data=data, content_type='application/json')

        self.assertEqual(response.json(),{'code': 2, 'info': 'Friend searched by id not exist'})
        
        # 成功
        aref = isFriend(user01, user00)
        self.assertTrue(aref)
        
        data={
            "friend_id": user00.user_id
        }
        response = self.client.post('/user/search_friend_by_id/', data=data, content_type='application/json')
        self.assertEqual(response.json(),
                         {
                            'code': 0, 
                            'info': 'Succeed', 
                            'user_id':user00.user_id, 
                            'avatar': user00.avatar,
                            'name': user00.name
                         })

    # by name
    def test_search_friend_by_name(self):
        # 登录user 
        login_data = {'name': 'testuser', 'password': '12345678'}
        login_someone(self, login_data)
        user01 = User.objects.get(name="testuser")
        user00 = User.objects.get(name="user000")
        # 失败 不存在此人
        data={
            'friend_name': "99999"
        }
        response = self.client.post('/user/search_friend_by_name/', data=data, content_type='application/json')

        self.assertEqual(response.json(),{'code': 2, 'info': 'Friend searched by name not exist'})
        
        
        userstanger = User.objects.create(name="stranger", password=make_password("password"))
        
        # 失败 非好友    
        data={
            'friend_name': userstanger.name
        }
        response = self.client.post('/user/search_friend_by_name/', data=data, content_type='application/json')
        self.assertEqual(response.json(),{'code': 2, 'info': "Friend you search not exist"})
        
        # 成功
        aref = isFriend(user01, user00)
        self.assertTrue(aref)
        
        data={
            "friend_name": user00.name
        }
        response = self.client.post('/user/search_friend_by_name/', data=data, content_type='application/json')
        self.assertEqual(response.json(),
                         {
                            'code': 0, 
                            'info': 'Succeed', 
                            'user_id':user00.user_id, 
                            'avatar': user00.avatar,
                            'name': user00.name
                         })


#! 好友列表
    def test_get_friends(self):
        data = {
            "name": "testuser", 
            "password": "12345678"
        }
        login_someone(self, data)
        response = self.client.get('/user/get_friends/', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        list = []
        for who in User.objects.all():
            if isFriend(User.objects.get(name="testuser"), who):
                list.append({
                    'avatar':who.avatar,
                    'name':who.name,
                    'user_id':who.user_id
                    })
        
        self.assertEqual(response.json(), {'code': 0, 'friends': list, 'info': 'Succeed'})

#! 用户列表        
    # users
    def test_users(self):
        # 创建两个用户
        request_data = {
            "name": "testuser11",
            "password": "newpassword11"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        request_data = {
            "name": "testuser22",
            "password": "newpassword22"
        }
        response = self.client.post(reverse("user-register"), data=request_data, content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # 获取用户列表并检查状态代码是否为200
        response = self.client.get("/user/users/")
        self.assertEqual(response.status_code, 200)

        # 检查返回的用户列表是否正确
        response_content = json.loads(response.content)
        self.assertEqual(len(response_content["users"]), 4)
