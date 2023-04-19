import json
from django.http import HttpRequest
from django.contrib.auth.hashers import make_password, check_password

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token

from user.models import User, Friendship, FriendshipRequest
from utils.utils_request import request_failed, request_success, return_field
from utils.utils_require import CheckLogin, require
from utils.utils_valid import *
from utils.utils_verify import *
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest


def check_for_user_data(body):
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    return name, password

class UserViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["POST"])
    def register(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        name, password = check_for_user_data(body)

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
    

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_password(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        old_password = body.get('old_pwd')
        new_password = body.get('new_pwd')

        if not check_password(old_password, user.password):
            return request_failed(2, "Wrong old password")

        if not password_valid(new_password):
            return request_failed(3, "Illegal new password")
        else:
            user.password = make_password(new_password)
        
        user.save()
        return request_success({"Modified": True})
    
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_avatar(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = get_user(req)
        new_avatar = body.get('avatar')

        user.avatar = new_avatar
        
        user.save()
        return request_success({"Modified": True})


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
