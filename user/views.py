import json
from django.http import HttpRequest
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token

from user.models import User, Friendship, FriendshipRequest, Group, GroupFriend
from msg.models import Conversation
from utils.utils_request import request_failed, request_success, return_field
from utils.utils_require import CheckLogin, require
from utils.utils_valid import *
from utils.utils_verify import *
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
import random

def check_for_user_data(body):
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    return name, password, email


# 检查用户输入的验证码是否和之前发送的一致
def check_code(user, code):
    if user.user_code == code:
        user.user_code = 0
        return True
    else:
        return False

class UserViewSet(viewsets.ViewSet):
#! 注册、登录、注销相关功能
    @action(detail=False, methods=["POST"])
    # 不用邮箱注册
    def register_without_email(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        name = require(body, "name", "string", err_msg="Missing or error type of [name]")
        password = require(body, "password", "string", err_msg="Missing or error type of [password]")

        if not name_valid(name):
            return request_failed(1, "Illegal username")
        elif name_exist(name):
            return request_failed(2, "Username already exists")    
        elif not password_valid(password):
            return request_failed(3, "Illegal password")        
        else: # Successful Create
            user = User(name=name)
            user.set_password(password)
            user.save()
        return request_success({"Created": True})



    @action(detail=False, methods=["POST"])
    # 注册时向邮箱发送验证码
    def send_email_for_register(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        
        # 基本信息格式校验
        name, password, email = check_for_user_data(body)
        
        if not name_valid(name):
            return request_failed(1, "Illegal username")
        elif name_exist(name):
            return request_failed(2, "Username already exists")    
        elif not password_valid(password):
            return request_failed(3, "Illegal password")
        elif not email_valid(email):
            return request_failed(4, "Illegal email")        
        
        # 新建一个用户
        user = User(name=name)
        user.set_password(password)
        user.user_email = email
        # 生成六位数字验证码
        code = random.randint(100000, 999999)
        user.user_code = code
        
        user.save()
        
        send_mail(
            'Verification Code',
            'Your verification code is: ' + str(code),
            '--kill se',
            [email])
    
    
    @action(detail=False, methods=["POST"])
    def register(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        name = body.get("name")
        user = User.objects.filter(name=name).first()
        
        if(check_code(user, body.get('code_input'))):
            # Successful Create
            return request_success({"Created": True})
        else:
            # 发一次验证码只能输入一次，输入错误就要重新发送验证码
            user.delete()
           
            
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def cancel_account(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        token = body.get("token")
        user = get_user(req)
        Token.objects.filter(key=token).delete()
        user.delete()
        return request_success({"Deleted": True})

    @action(detail=False, methods=["POST"])
    def auto_login(self, req: HttpRequest):
        if get_user(req):
            return request_success({"Logged in": True})
        else:
            return request_failed(1, "Not logged in yet")
              
    @action(detail=False, methods=["POST"])
    def login(self, req: HttpRequest):
        print("Hey, what's wrong???")
        body = json.loads(req.body.decode("utf-8"))
        name = body.get('name')
        password = body.get('password')

        if not name_valid(name):
            return request_failed(1, "Illegal username")
        user = name_exist(name)
        if not user:
            return request_failed(2, "User does not exist")
        if not user.check_password(password):
            return request_failed(3, "Wrong password")
        if verify_user(user):
            Token.objects.filter(user=user).delete()
        
        # Successful login
        print(user.user_id)
        token = Token.objects.update_or_create(user=user)
        token = Token.objects.get(user=user).key
        print(token)
        return request_success({"Logged in": True, "Token": token})
        
          
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def logout(self, req: HttpRequest):
        body = json.loads(req.body)
        token = body.get("token")
        Token.objects.filter(key=token).delete()
        return request_success({'Logged out': True})

#! 修改个人信息相关功能        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_name(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        new_name = body.get('name')

        if not name_valid(new_name):
            return request_failed(2, "Illegal username")
        elif name_exist(new_name):
            return request_failed(3, "Username already exists")
        else:
            user.name = new_name

        user.save()
        return request_success({"Modified": True})
    
        # 注册时向邮箱发送验证码
    
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 为了修改密码 发送验证码
    def send_email_for_changepwd(self, req: HttpRequest):
        # 新的格式正确性校验
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        old_password = body.get('old_pwd')

        # 旧的密码正确性校验
        if not user.check_password(old_password):
            return request_failed(2, "Wrong old password")
        
        email = user.user_email
        
        # 生成六位数字验证码
        code = random.randint(100000, 999999)
        user.user_code = code
        
        user.save()
        
        send_mail(
            'Verification Code',
            'Your verification code is: ' + str(code),
            '--kill se',
            [email])
    
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 输入验证码后点击的确认按钮
    def reset_password(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        new_password = body.get('new_pwd')
        if check_code(get_user(req), body.get('code_input')):
            user = get_user(req)
            user.password = make_password(new_password)
            user.save()
            return request_success({"Modified": True})
        else:
            return request_failed(1, "Wrong verification code")

    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_avatar(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        new_avatar = body.get('avatar')

        user.avatar = new_avatar
        
        user.save()
        return request_success({"Modified": True})

#! 加好友相关功能
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_friend_requests(self, req: HttpRequest):
        user = get_user(req)

        request_list = FriendshipRequest.objects.filter(friend_user_id=user.user_id)
        friend_id_list = [request.user_id for request in request_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]
        
        return_data = {
            "requests": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)

    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def send_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()
        if not friend:
            return request_failed(1, "target Friend not exist")
        
        if isFriend(user, friend):
            return request_failed(2, "Already become friends")
        
        if requestExists(user, friend):
            return request_failed(3, "Request already exists")
        elif requestExists(friend, user): 
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends successfully": True})
        
        sendFriendRequest(user, friend)
        return request_success({"Send request": True})
 
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def respond_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()
        if not friend:
            return request_failed(1, "Friend not exist")
        
        if not requestExists(friend, user):
            return request_failed(2, "Friend request doesn't exist")
        response = body.get('response')

        if response == "accept":
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends": True})
        elif response == "reject":
            requestExists(friend, user).delete()
            return request_success({"Become Friends": False})
        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def del_friend(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_id)

        if not friend:
            return request_failed(2, "your Friend not exist")
        
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).first()
        if not friendship:
            return request_failed(3, "Not your friend")
        
        Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).delete()
        Friendship.objects.filter(user_id=friend_id, friend_user_id=user.user_id).delete()
        return request_success({"Deleted": True})
           
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_profile(self, req: HttpRequest):
        user = get_user(req)

        return_data = return_field(user.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
       
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_by_id(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()

        if not friend:
            return request_failed(2, "User searched by id not exist")
        
        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_by_name(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        friend_name = body.get('friend_name')
        friend = User.objects.filter(name=friend_name).first()

        if not friend:
            return request_failed(2, "User searched by name not exist")
        
        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_friends(self, req: HttpRequest):
        user = get_user(req)
        friendship_list = Friendship.objects.filter(user_id=user.user_id)
        friend_id_list = [friendship.friend_user_id for friendship in friendship_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]

        return_data = {
            "friends": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_friend_by_id(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get('friend_id')

        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(2, "Friend searched by id not exist")
        else:
            friend = User.objects.filter(user_id=friend_id).first()

        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])

        return request_success(return_data)
       
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def search_friend_by_name(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        friend_name = body.get('friend_name')

        friend = User.objects.filter(name=friend_name).first()
        if not friend:
            return request_failed(2, "Friend searched by name not exist")
        
        friend_id = friend.user_id
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(2, "Friend you search not exist")

        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])

        return request_success(return_data)

#! 分组相关功能
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 创建分组
    def create_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_name = body.get('name')
        group = Group.objects.filter(group_name=group_name).first()
        if group:
            return request_failed(2, "Group name already exists")
        
        new_group = Group.objects.create(group_name=group_name, admin_id=user.user_id) #admin是拥有这个群组的人
        new_group.save()
        new_group_id = new_group.group_id
        # 返回group_id
        return request_success({"group_id": new_group_id})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 删除分组
    def del_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        group = Group.objects.filter(group_id=group_id).first()
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")
        
        Group.objects.filter(group_id=group_id).delete()
        return request_success({"Deleted": True})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 获取分组
    def get_group(self, req: HttpRequest):
        user = get_user(req)
        group_list = Group.objects.filter(admin_id=user.user_id)
        return_data = {
            "groups": [
                return_field(group.serialize(), ["group_id", "group_name", "admin_id"])
            for group in group_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 获取某组内的好友
    def get_group_friends(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        group = Group.objects.filter(group_id=group_id).first()
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")
        
        # 返回这个组内的所有好友
        group_friend_list = GroupFriend.objects.filter(group_id=group_id)
        friend_id_list = [group_friend.friend_user_id for group_friend in group_friend_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]

        return_data = {
            "friends": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 添加好友到分组
    def add_friend_to_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        friend_id = body.get('friend_id')
        group = Group.objects.filter(group_id=group_id).first()
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")
        
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(4, "Friend not exist")
        
        group_friend = GroupFriend.objects.filter(group_id=group_id, friend_user_id=friend_id)
        if group_friend:
            return request_failed(5, "Friend already in this group")
        
        new_group_friend = GroupFriend.objects.create(group_id=group_id, friend_user_id=friend_id)
        new_group_friend.save()
        return request_success({"Added": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    # 从分组中删除好友
    def del_friend_from_group(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode("utf-8"))
        group_id = body.get('group_id')
        friend_id = body.get('friend_id')
        group = Group.objects.filter(group_id=group_id).first()
        if not group:
            return request_failed(2, "Group not exist")
        if group.admin_id != user.user_id:
            return request_failed(3, "You are not admin of this group")
        
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(4, "Friend not exist")
        
        group_friend = GroupFriend.objects.filter(group_id=group_id, friend_user_id=friend_id)
        if not group_friend:
            return request_failed(5, "Friend not in this group")
        
        GroupFriend.objects.filter(group_id=group_id, friend_user_id=friend_id).delete()
        return request_success({"Deleted": True})
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_private_conversations(self, req: HttpRequest):
        user = get_user(req)
        private_conversation_list = Conversation.objects.filter(members__in=[user], is_Private=True)
        # May be of little efficiency
        r_member_list = [x.members.all() for x in private_conversation_list]
        members = []
        for member_list in r_member_list:
            members += member_list
        # deduplicate
        members = list(set(members))
        members.remove(user)
        
        return_data = {
            "conversations": [ 
                {
                    "id": conversation.conversation_id,
                    "friend_id": friend.user_id,
                    "friend_name": friend.name,
                    "friend_avatar": friend.avatar
                }
                for conversation, friend in zip(private_conversation_list, members)
            ]
        }
        return request_success(return_data)

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def get_or_create_private_conversation(self, req: HttpRequest):
        user = get_user(req)
        body = json.loads(req.body.decode('utf-8'))
        friend_id = body.get('friend')
        friend = User.objects.filter(user_id=friend_id).first()
        if not friend:
            return request_failed(2, "Friend does not exist")
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).first()
        if not friendship:
            return request_failed(3, "You are not friends")
        # Successful get
        if Conversation.objects.filter(members__in=[user], is_Private=True).filter(members__in=[friend]).first():
            print("HI")
            conversation = Conversation.objects.filter(members__in=[user], is_Private=True).filter(members__in=[friend]).first()
            return request_success({"conversation_id": conversation.conversation_id})
        # Successful create
        conversation = Conversation.objects.create(is_Private=True)
        conversation.save()
        conversation.members.add(user, friend)
        return request_success({"conversation_id": conversation.conversation_id})

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def create_group_conversation(self, req: HttpRequest):
        pass
